"""
NSFW (Not Safe For Work) content detection module.
This module uses the NudeNet library to perform local, offline detection.
"""
import os
import tempfile
from nudenet import NudeDetector

class NSFWDetector:
    """
    A class that uses the NudeNet library to detect NSFW content in images.
    """

    # These are the labels that NudeNet classifies as "unsafe".
    # We are being conservative and blocking anything that isn't explicitly safe.
    # NudeNet labels include: 'EXPOSED_BELLY', 'EXPOSED_BUTTOCKS', 'EXPOSED_BREAST',
    # 'EXPOSED_GENITALIA', 'COVERED_BELLY', 'COVERED_BUTTOCKS', 'COVERED_BREAST',
    # 'COVERED_GENITALIA', 'FACE_FEMALE', 'FACE_MALE'.
    UNSAFE_LABELS = [
        'EXPOSED_BUTTOCKS', 'EXPOSED_BREAST', 'EXPOSED_GENITALIA',
        'COVERED_BUTTOCKS', 'COVERED_BREAST', 'COVERED_GENITALIA'
    ]

    # Confidence threshold for flagging an image.
    CONFIDENCE_THRESHOLD = 0.6

    def __init__(self):
        """
        Initializes the NudeDetector.
        The model files for NudeNet will be downloaded automatically to the
        user's home directory the first time this is instantiated.
        """
        print("INFO: Initializing NudeNet NSFWDetector. This may take a moment on first run...")
        # Note: By default, NudeNet downloads models to ~/.NudeNet/
        self.detector = NudeDetector()
        print("INFO: NudeNet NSFWDetector initialized.")

    def is_image_safe(self, image_bytes: bytes) -> (bool, str):
        """
        Analyzes the given image bytes for NSFW content.

        This method saves the image bytes to a temporary file, runs detection,
        and then cleans up the file.

        Args:
            image_bytes: The image content as a byte string.

        Returns:
            A tuple containing:
            - A boolean indicating if the image is safe (True) or not (False).
            - A string providing the reason for the determination.
        """
        # NudeNet's detect method requires a file path, so we create a temporary file.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            filepath = tmp.name

        try:
            # Perform detection on the temporary file.
            results = self.detector.detect(filepath)

            # Check the results against our criteria.
            for detection in results:
                label = detection.get('label', '').upper()
                score = detection.get('score', 0)

                if label in self.UNSAFE_LABELS and score >= self.CONFIDENCE_THRESHOLD:
                    # If any unsafe label is found above the threshold, reject the image.
                    reason = f"Unsafe content detected: '{label}' with {score:.2f} confidence."
                    print(f"WARN: {reason}")
                    return False, reason

            # If no unsafe labels are found, the image is considered safe.
            return True, "Image is safe."

        except Exception as e:
            # In case of an error during detection, log it and fail safe (reject image).
            print(f"ERROR: An error occurred during NSFW detection: {e}")
            return False, "An error occurred during content analysis."
        finally:
            # Ensure the temporary file is always deleted.
            if os.path.exists(filepath):
                os.remove(filepath)
