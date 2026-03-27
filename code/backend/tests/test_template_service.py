from app.services.template_service import render_template


def test_render_template_success():
    content = "Hello {{name}}"
    result = render_template(content, {"name": "Alice"})
    assert result == "Hello Alice"
