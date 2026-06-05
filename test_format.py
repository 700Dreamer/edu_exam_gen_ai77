import yaml
import os

prompt_path = os.path.join("core", "prompts", "exam_generator.yaml")
with open(prompt_path, 'r') as f:
    prompt_template = yaml.safe_load(f)["template"]

try:
    prompt = prompt_template.format(
        subject="TEST",
        level="TEST",
        term="TEST",
        topic="TEST",
        syllabus_rows="TEST",
        rubric_context="TEST",
        pkg_skills_str="TEST",
        pkg_prereqs_str="TEST",
        age_profile="TEST",
        authorized_topics_str="TEST",
        authoritative_commands_rule="TEST",
        prep_req="TEST",
        tikz_rule_local="TEST",
        mcq_routing_rule="TEST",
        chunk_size=10,
        start_num=1,
        layout_instruction="TEST"
    )
    print("Format successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
