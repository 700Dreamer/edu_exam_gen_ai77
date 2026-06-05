import yaml
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Union, Dict, Any, Optional

import os as _os

def load_curriculum_config():
    _config_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "config", "ecd_curriculum.yaml")
    with open(_config_path, "r") as f:
        return yaml.safe_load(f)

def get_nursery_schema(class_level: str, learning_area: str) -> type[BaseModel]:
    config = load_curriculum_config()
    class_config = config["classes"].get(class_level, config["classes"]["Middle Class"])
    
    if learning_area == "LA4":
        allowed_types = class_config["allowed_math_types"]
    elif learning_area == "LA5":
        allowed_types = class_config["allowed_language_types"]
    else:
        allowed_types = class_config["allowed_social_types"]
        
    QuestionTypeEnum = Enum("QuestionType", {t: t for t in allowed_types})
    
    class QuestionItem(BaseModel):
        picture: Optional[str] = Field(None, description="The object to draw. MUST be simple text like 'apple', not emojis.")
        count: Optional[int] = Field(None, description="Number of items. Max limit depends on class level.")
        options: Optional[List[int]] = Field(None, description="Multiple choice options")

    class Sequence(BaseModel):
        given: List[int] = Field(..., description="The given numbers in the sequence")
        blank_at: int = Field(..., description="The missing number")
        after: List[int] = Field(..., description="The numbers after the blank")
        
    class MathSum(BaseModel):
        a: int
        b: int

    class SetItem(BaseModel):
        count_word: str
        object: str
        hint: Optional[str] = None
        
    class OddGroup(BaseModel):
        words: List[str]
        
    class NumPair(BaseModel):
        number: int
        
    class QuestionContent(BaseModel):
        items: Optional[List[QuestionItem]] = None
        sequences: Optional[List[Sequence]] = None
        sums: Optional[List[MathSum]] = None
        left: Optional[List[str]] = Field(None, description="Left side for matching")
        right: Optional[List[str]] = Field(None, description="Right side for matching")
        numbers: Optional[List[int]] = Field(None, description="Numbers for shading/drawing")
        sets: Optional[List[SetItem]] = None
        shapes: Optional[List[str]] = Field(None, description="Names of shapes")
        words: Optional[List[str]] = Field(None, description="List of words for copy_word, make_sentence, fill_missing_letter, fill_missing_word, and write_yes_no")
        letters: Optional[List[str]] = Field(None, description="List of letters for trace_letter")
        groups: Optional[List[OddGroup]] = Field(None, description="Groups of words for odd_one_out")
        pairs: Optional[List[NumPair]] = Field(None, description="Number pairs for write_number_names")
        options: Optional[List[str]] = Field(None, description="Options to choose from (e.g. for circle_correct)")
        statements: Optional[List[str]] = Field(None, description="Statements for write_yes_no or oral_questions")

    class Question(BaseModel):
        number: int
        instruction: str = Field(..., description="Simple, child-friendly instruction")
        type: QuestionTypeEnum = Field(..., description="The type of question.")
        content: QuestionContent
        
        
    class ExamSchema(BaseModel):
        questions: List[Question] = Field(..., description="List of precisely 8 questions")
        
    return ExamSchema

def get_critic_schema(class_level: str, learning_area: str) -> type[BaseModel]:
    ExamSchema = get_nursery_schema(class_level, learning_area)
    
    class CriticReview(BaseModel):
        passed: bool = Field(description="True if the drafted exam perfectly adheres to the cognitive constraints and vocabulary rules. False otherwise.")
        feedback: str = Field(description="If passed=False, explain exactly what was wrong with the instructions or vocabulary. If passed=True, output 'Perfect'.")
        revised_exam: ExamSchema = Field(description="The final, corrected exam. If passed=True, just output the exact same drafted exam.")
        
    return CriticReview
