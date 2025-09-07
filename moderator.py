"""
Placeholder module for NSFW (Not Safe For Work) content detection.
"""

class NSFWDetector:
    """
    A placeholder for a real NSFW content detection model.

    This default implementation considers all images to be safe. It is intended
    to allow the application to be fully runnable without requiring heavy
    machine learning libraries or API keys for a real detection service.

    In a production environment, this class should be replaced with a proper
    implementation that uses a trained model (e.g., using TensorFlow, PyTorch)
    or an external API to classify image content.
    """
    def __init__(self):
        """
        In a real implementation, this is where the detection model would be
        loaded into memory. For now, it just prints an informational message.
        """
        print("INFO: Initializing placeholder NSFWDetector. All images will be considered safe.")

    def is_image_safe(self, image_bytes: bytes) -> (bool, str):
        """
        Analyzes the given image bytes for NSFW content.

        Args:
            image_bytes: The image content as a byte string.

        Returns:
            A tuple containing:
            - A boolean indicating if the image is safe (True) or not (False).
            - A string providing the reason for the determination.
        """
        # This placeholder implementation always returns True.
        # It does not actually analyze the image bytes.
        return True, "Image is safe (Note: using placeholder NSFW detector)."
