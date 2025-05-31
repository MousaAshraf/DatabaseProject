import pytest
from core.security import generate_qr_code


def test_generate_qr_code_valid():
    qr_data = "test_data_123"
    qr_code = generate_qr_code(qr_data)
    assert qr_code.startswith("data:image/png;base64,")
    assert len(qr_code) > 100


@pytest.mark.parametrize("invalid_input", ["", None, 123, "   "])
def test_generate_qr_code_invalid(invalid_input):
    with pytest.raises(ValueError):
        generate_qr_code(invalid_input)
