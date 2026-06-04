"""Image handling with validation, resizing, cropping, and cleanup"""

import os
import logging
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import magic

from core.constants import PROFILE_PICTURE_STORAGE_PATH

logger = logging.getLogger("gunicorn.access")


class ImageHandler:
    """Handles image validation, processing, storage, and cleanup"""

    # Configuration
    ALLOWED_FORMATS = ("image/jpeg", "image/png")
    MAX_WIDTH = 8192
    MAX_HEIGHT = 8192
    MIN_WIDTH = 200
    MIN_HEIGHT = 200
    THUMBNAIL_WIDTH = 50
    THUMBNAIL_HEIGHT = 50
    QUALITY = 85

    def __init__(self, storage_path=PROFILE_PICTURE_STORAGE_PATH):
        """Initialize image handler with storage path"""
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def validate(self, data: bytes) -> bool:
        """Validate image format and integrity

        Parameters:
            data: Raw image bytes

        Returns:
            True if image is valid, False otherwise
        """
        try:
            # Check MIME type
            content_type = magic.from_buffer(data, mime=True)
            if content_type not in self.ALLOWED_FORMATS:
                logger.warning("Invalid image format: %s", content_type)
                return False

            logger.debug("Image format verified: %s", content_type)

            # Check image integrity
            image = Image.open(BytesIO(data))
            image.verify()
            logger.debug("Image integrity verified")

            return True

        except UnidentifiedImageError:
            logger.error("Error: Tampered or corrupted image file")
            return False
        except OSError:
            logger.error("Error: Image file is truncated")
            return False
        except Exception as e:
            logger.error("Error validating image: %s", e)
            return False

    def check_dimensions(self, image: Image.Image) -> bool:
        """Check if image dimensions are within acceptable range

        Parameters:
            image: PIL Image object

        Returns:
            True if dimensions are acceptable, False otherwise
        """
        width, height = image.size

        if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
            logger.warning(
                "Image too small: %dx%d (min: %dx%d)",
                width,
                height,
                self.MIN_WIDTH,
                self.MIN_HEIGHT,
            )
            return False

        if width > self.MAX_WIDTH or height > self.MAX_HEIGHT:
            logger.warning(
                "Image too large: %dx%d (max: %dx%d)",
                width,
                height,
                self.MAX_WIDTH,
                self.MAX_HEIGHT,
            )
            return False

        logger.debug("Image dimensions verified: %dx%d", width, height)
        return True

    def crop_to_square(self, image: Image.Image) -> Image.Image:
        """Crop image to square by removing edges

        Parameters:
            image: PIL Image object

        Returns:
            Cropped PIL Image object
        """
        width, height = image.size
        size = min(width, height)

        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size

        cropped = image.crop((left, top, right, bottom))
        logger.debug("Image cropped to square: %dx%d", size, size)
        return cropped

    def resize(self, image: Image.Image, width: int, height: int) -> Image.Image:
        """Resize image to specified dimensions

        Parameters:
            image: PIL Image object
            width: Target width
            height: Target height

        Returns:
            Resized PIL Image object
        """
        resized = image.resize((width, height), Image.Resampling.LANCZOS)
        logger.debug("Image resized to %dx%d", width, height)
        return resized

    def generate_thumbnail(self, image: Image.Image) -> Image.Image:
        """Generate thumbnail from image

        Parameters:
            image: PIL Image object

        Returns:
            Thumbnail PIL Image object
        """
        thumb = image.copy()
        thumb.thumbnail(
            (self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT),
            Image.Resampling.LANCZOS,
        )
        logger.debug(
            "Thumbnail generated: %dx%d", self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT
        )
        return thumb

    def save_image(
        self, data: bytes, filename: str, generate_thumbnail: bool = False
    ) -> dict:
        """Process, validate, and save image

        Parameters:
            data: Raw image bytes
            filename: Filename to save as
            generate_thumbnail: Whether to generate thumbnail

        Returns:
            Dict with 'success' status and 'paths' containing saved file paths
        """
        result = {"success": False, "paths": {}, "error": None}

        # Validate
        if not self.validate(data):
            result["error"] = "Image validation failed"
            return result

        try:
            # Open and check dimensions
            image = Image.open(BytesIO(data))

            if not self.check_dimensions(image):
                result["error"] = "Image dimensions out of range"
                return result

            # Crop to square
            image = self.crop_to_square(image)

            # Resize to standard size
            image = self.resize(image, self.MIN_WIDTH, self.MIN_HEIGHT)

            # Save main image
            main_path = os.path.join(self.storage_path, filename)
            image.save(main_path, quality=self.QUALITY, optimize=True)
            result["paths"]["main"] = main_path

            logger.info("Image saved: %s", main_path)

            # Generate and save thumbnail if requested
            if generate_thumbnail:
                thumb = self.generate_thumbnail(image)
                thumb_filename = f"thumb_{filename}"
                thumb_path = os.path.join(self.storage_path, thumb_filename)
                thumb.save(thumb_path, quality=self.QUALITY, optimize=True)
                result["paths"]["thumbnail"] = thumb_path
                logger.info("Thumbnail saved: %s", thumb_path)

            result["success"] = True
            return result

        except Exception as e:
            logger.error("Error saving image: %s", e)
            result["error"] = str(e)
            return result

    def delete_image(self, filename: str, delete_thumbnail: bool = False) -> bool:
        """Delete image file from storage

        Parameters:
            filename: Filename to delete
            delete_thumbnail: Whether to also delete thumbnail

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            file_path = os.path.join(self.storage_path, filename)

            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Image deleted: %s", file_path)
            else:
                logger.debug("Image file not found: %s", file_path)

            # Delete thumbnail if requested
            if delete_thumbnail:
                thumb_path = os.path.join(self.storage_path, f"thumb_{filename}")
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                    logger.info("Thumbnail deleted: %s", thumb_path)

            return True

        except OSError as e:
            logger.error("Error deleting image: %s", e)
            return False

    def get_image_path(self, filename: str) -> str:
        """Get full path to image file

        Parameters:
            filename: Image filename

        Returns:
            Full path to image file
        """
        return os.path.join(self.storage_path, filename)
