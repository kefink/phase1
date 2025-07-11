"""
Service for handling mark conversions and calculations.
"""

class MarkConversionService:
    """
    Service for converting between raw marks and percentages.
    This centralizes all mark conversion logic to ensure consistency.
    """

    @staticmethod
    def calculate_percentage(raw_mark, max_raw_mark):
        """
        Calculate percentage from raw mark and maximum raw mark.

        Args:
            raw_mark (float): The raw mark achieved
            max_raw_mark (float): The maximum possible raw mark

        Returns:
            float: The calculated percentage (0-100)
        """
        if max_raw_mark <= 0:
            return 0

        percentage = (raw_mark / max_raw_mark) * 100
        # Round to 1 decimal place
        return round(percentage * 10) / 10

    @staticmethod
    def validate_raw_mark(raw_mark, max_raw_mark):
        """
        Validate that a raw mark is within acceptable range and doesn't result in a percentage > 100%.

        Args:
            raw_mark (float): The raw mark to validate
            max_raw_mark (float): The maximum possible raw mark

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            raw_mark = float(raw_mark)
            max_raw_mark = float(max_raw_mark)

            # Enforce reasonable limits on raw marks and max_raw_mark
            # No subject should have more than 1000 marks as a maximum
            if max_raw_mark > 1000:
                return False

            # Check if raw mark is within range (0 to max_raw_mark)
            if not (0 <= raw_mark <= max_raw_mark):
                return False

            # Calculate percentage and ensure it doesn't exceed 100%
            percentage = (raw_mark / max_raw_mark) * 100 if max_raw_mark > 0 else 0
            return percentage <= 100
        except (ValueError, TypeError):
            return False

    @staticmethod
    def sanitize_raw_mark(raw_mark, max_raw_mark):
        """
        Sanitize a raw mark to ensure it's within acceptable range.
        If the mark is invalid, it will be adjusted to a valid value.

        Args:
            raw_mark (float): The raw mark to sanitize
            max_raw_mark (float): The maximum possible raw mark

        Returns:
            tuple: (sanitized_raw_mark, sanitized_max_raw_mark)
        """
        import logging
        logger = logging.getLogger('mark_validation')

        original_raw_mark = raw_mark
        original_max_raw_mark = max_raw_mark

        try:
            raw_mark = float(raw_mark)
            max_raw_mark = float(max_raw_mark)

            # Enforce reasonable limits on max_raw_mark (cap at 1000)
            if max_raw_mark > 1000:
                logger.warning(f"Max raw mark {max_raw_mark} exceeds limit of 1000. Capping to 1000.")
                max_raw_mark = 1000

            # Enforce minimum value for max_raw_mark
            if max_raw_mark < 1:
                logger.warning(f"Max raw mark {max_raw_mark} is less than 1. Setting to default of 100.")
                max_raw_mark = 100

            # Ensure raw_mark is within range (0 to max_raw_mark)
            if raw_mark < 0:
                logger.warning(f"Raw mark {raw_mark} is negative. Setting to 0.")
                raw_mark = 0
            elif raw_mark > max_raw_mark:
                logger.warning(f"Raw mark {raw_mark} exceeds max raw mark {max_raw_mark}. Capping to {max_raw_mark}.")
                raw_mark = max_raw_mark

            # Log if significant changes were made
            if (original_raw_mark != raw_mark or original_max_raw_mark != max_raw_mark):
                logger.info(f"Mark sanitized: original ({original_raw_mark}/{original_max_raw_mark}) -> sanitized ({raw_mark}/{max_raw_mark})")

            return raw_mark, max_raw_mark
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting mark values: {e}. raw_mark={original_raw_mark}, max_raw_mark={original_max_raw_mark}")
            # Return safe defaults if conversion fails
            return 0, 100

    @staticmethod
    def get_performance_category(percentage):
        """
        Convert a percentage to a performance category.

        Args:
            percentage (float): The percentage score (0-100)

        Returns:
            str: Performance category (EE1, EE2, ME1, ME2, AE1, AE2, BE1, BE2)
        """
        if percentage >= 90:
            return "EE1"  # Exceeding Expectation 1
        elif percentage >= 75:
            return "EE2"  # Exceeding Expectation 2
        elif percentage >= 58:
            return "ME1"  # Meeting Expectation 1
        elif percentage >= 41:
            return "ME2"  # Meeting Expectation 2
        elif percentage >= 31:
            return "AE1"  # Approaching Expectation 1
        elif percentage >= 21:
            return "AE2"  # Approaching Expectation 2
        elif percentage >= 11:
            return "BE1"  # Below Expectation 1
        else:
            return "BE2"  # Below Expectation 2

    @staticmethod
    def get_performance_remarks(percentage):
        """
        Generate detailed performance remarks based on percentage.

        Args:
            percentage (float): The percentage score (0-100)

        Returns:
            str: Detailed performance remarks
        """
        if percentage >= 90:
            return "EE1"  # Exceeding Expectation 1
        elif percentage >= 75:
            return "EE2"  # Exceeding Expectation 2
        elif percentage >= 58:
            return "ME1"  # Meeting Expectation 1
        elif percentage >= 41:
            return "ME2"  # Meeting Expectation 2
        elif percentage >= 31:
            return "AE1"  # Approaching Expectation 1
        elif percentage >= 21:
            return "AE2"  # Approaching Expectation 2
        elif percentage >= 11:
            return "BE1"  # Below Expectation 1
        else:
            return "BE2"  # Below Expectation 2
