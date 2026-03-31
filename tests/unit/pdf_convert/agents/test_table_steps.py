"""Tests for table step helpers."""

from unittest.mock import patch

from gm_kit.pdf_convert.agents.table_steps import (
    bbox_points_to_pixels,
    build_step_7_7_input_payload,
    build_step_7_7_vision_payload,
    build_step_8_7_input_payload,
)


class TestBuildStep7_7Payload:
    """Test step 7.7 input payload building."""

    def test_builds_text_scan_payload(self, tmp_path):
        """Should build payload for text scan phase."""
        payload = build_step_7_7_input_payload(
            pdf_path="/path/to/test.pdf",
            page_num=4,  # 0-based, will be 5 in output
            extracted_text="Sample page text",
            workspace=str(tmp_path),
            dpi=150,
        )

        assert payload["step_id"] == "7.7"
        assert payload["output_contract"] == "schemas/step_7_7.schema.json"
        assert payload["page_number_1based"] == 5
        assert payload["phase"] == "text_scan"
        assert payload["dpi"] == 150
        assert "page_images" in payload["page_image"]

    def test_uses_env_dpi_default(self, tmp_path):
        """Should use GM_PAGE_IMAGE_DPI from environment."""
        with patch.dict("os.environ", {"GM_PAGE_IMAGE_DPI": "200"}):
            payload = build_step_7_7_input_payload(
                pdf_path="/path/to/test.pdf",
                page_num=0,
                extracted_text="text",
                workspace=str(tmp_path),
            )

        assert payload["dpi"] == 200

    def test_builds_vision_payload_with_output_contract(self, tmp_path):
        """Should include output contract for vision-confirmation payloads."""
        page_images_dir = tmp_path / "page_images"
        page_images_dir.mkdir(parents=True)
        page_image = page_images_dir / "page_002.png"
        page_image.write_bytes(b"fake")

        payloads = build_step_7_7_vision_payload(
            pdf_path="/path/to/test.pdf",
            page_num=1,
            detected_tables=[{"table_id": "page_002_table_001", "text_context": "Weapons table"}],
            workspace=str(tmp_path),
            dpi=150,
        )

        assert len(payloads) == 1
        payload = payloads[0]
        assert payload["step_id"] == "7.7"
        assert payload["output_contract"] == "schemas/step_7_7.schema.json"
        assert payload["phase"] == "vision_confirmation"


class TestBuildStep8_7Payload:
    """Test step 8.7 input payload building."""

    def test_builds_conversion_payload(self, tmp_path):
        """Should build payload for table conversion."""
        table_data = {
            "table_id": "t1",
            "page_number_1based": 5,
            "bbox_pixels": {"x0": 100, "y0": 200, "x1": 500, "y1": 400},
        }

        # Create a dummy image file for the test
        from PIL import Image

        img = Image.new("RGB", (100, 100), color="white")
        page_image_path = tmp_path / "page_5.png"
        img.save(page_image_path)

        payload = build_step_8_7_input_payload(
            table_data=table_data,
            page_image_path=str(page_image_path),
            flat_text_path="tests/fixtures/table_text.txt",
            workspace=str(tmp_path),
            dpi=150,
        )

        assert payload["step_id"] == "8.7"
        assert payload["output_contract"] == "schemas/step_8_7.schema.json"
        assert payload["table_id"] == "t1"
        assert payload["bbox_pixels"]["x0"] == 100
        assert "table_crops" in payload["table_crop_image"]


class TestBboxConversion:
    """Test coordinate conversion."""

    def test_points_to_pixels(self):
        """Should convert PDF points to pixels correctly."""
        bbox_points = {"x0": 72, "y0": 72, "x1": 144, "y1": 144}

        result = bbox_points_to_pixels(
            bbox_points=bbox_points,
            page_width_pts=612,  # 8.5 inch letter
            page_height_pts=792,  # 11 inch letter
            image_width_px=1275,  # 8.5 * 150 DPI
            image_height_px=1650,  # 11 * 150 DPI
        )

        # At 150 DPI, 72 points (1 inch) = 150 pixels
        assert result["x0"] == 150
        assert result["y0"] == 150
        assert result["x1"] == 300
        assert result["y1"] == 300
