import json
from ui.nursery_builder import build_nursery_html

exam_data = {
    "class_level": "Baby Class",
    "learning_area": "LA4",
    "la_name": "MATHEMATICAL CONCEPTS",
    "questions": [
        {
            "number": 1,
            "instruction": "Count and write.",
            "type": "count_write",
            "content": {
                "items": [
                    {"picture": "tree", "count": 4},
                    {"picture": "pencil", "count": 8},
                    {"picture": "box", "count": 0},
                    {"picture": "sweet", "count": 2}
                ]
            }
        }
    ]
}

images = {
    "tree": "data:image/png;base64,123",
    "pencil": "data:image/png;base64,123",
    "box": "data:image/png;base64,123",
    "sweet": "data:image/png;base64,123"
}

html = build_nursery_html(exam_data, images)
with open("test_zero.html", "w") as f:
    f.write(html)
print("Done")
