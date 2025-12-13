import { describe, it, expect } from "vitest";
import { validateGeneralQuestions } from "../validation";
import { GENERAL_QUESTION_KEYS } from "../../config/generalQuestions";

describe("validateGeneralQuestions", () => {
  describe("job-level validation", () => {
    it("should return error if job-level is missing", () => {
      const formData = {};
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[0]]).toBe(
        "Please select at least one job level option."
      );
    });

    it("should return error if job-level is empty array", () => {
      const formData = { [GENERAL_QUESTION_KEYS[0]]: [] };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[0]]).toBe(
        "Please select at least one job level option."
      );
    });

    it("should return error if more than 2 job levels selected", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level", "Intermediate", "Entry"],
      };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[0]]).toBe(
        "Please select at most two job level options."
      );
    });

    it("should return error if 2 non-adjacent job levels selected", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level", "Entry"],
      };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[0]]).toContain(
        "must be adjacent"
      );
    });

    it("should pass validation for single job level", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "1",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
        "additional-info": "Test description",
      };
      const result = validateGeneralQuestions(formData);
      expect(result.errors[GENERAL_QUESTION_KEYS[0]]).toBeUndefined();
    });

    it("should pass validation for 2 adjacent job levels", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level", "Intermediate"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "1",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
        "additional-info": "Test description",
      };
      const result = validateGeneralQuestions(formData);
      expect(result.errors[GENERAL_QUESTION_KEYS[0]]).toBeUndefined();
    });
  });

  describe("job-boards validation", () => {
    it("should return error if job-boards is missing", () => {
      const formData = {};
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[1]]).toBe(
        "Please select at least one job board."
      );
    });

    it("should return error if job-boards is empty array", () => {
      const formData = { [GENERAL_QUESTION_KEYS[1]]: [] };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[1]]).toBe(
        "Please select at least one job board."
      );
    });

    it("should pass validation for valid job-boards", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori", "Jobly"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "1",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
        "additional-info": "Test description",
      };
      const result = validateGeneralQuestions(formData);
      expect(result.errors[GENERAL_QUESTION_KEYS[1]]).toBeUndefined();
    });
  });

  describe("deep-mode validation", () => {
    it("should return error if deep-mode is missing", () => {
      const formData = {};
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[2]]).toBe(
        "Please select an option."
      );
    });

    it("should return error if deep-mode is empty string", () => {
      const formData = { [GENERAL_QUESTION_KEYS[2]]: "" };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[2]]).toBe(
        "Please select an option."
      );
    });

    it("should pass validation for valid deep-mode", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "1",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
        "additional-info": "Test description",
      };
      const result = validateGeneralQuestions(formData);
      expect(result.errors[GENERAL_QUESTION_KEYS[2]]).toBeUndefined();
    });
  });

  describe("cover-letter-num validation", () => {
    it("should return error if cover-letter-num is missing", () => {
      const formData = {};
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[3]]).toBe(
        "Please select an option."
      );
    });

    it("should pass validation for valid cover-letter-num", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "5",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
        "additional-info": "Test description",
      };
      const result = validateGeneralQuestions(formData);
      expect(result.errors[GENERAL_QUESTION_KEYS[3]]).toBeUndefined();
    });
  });

  describe("cover-letter-style validation", () => {
    it("should return error if cover-letter-style is missing", () => {
      const formData = {};
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[4]]).toBe(
        "Please select at least one option."
      );
    });

    it("should return error if more than 2 styles selected", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[4]]: ["Professional", "Friendly", "Confident"],
      };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors[GENERAL_QUESTION_KEYS[4]]).toBe(
        "Please select at most two options."
      );
    });

    it("should pass validation for 1 or 2 styles", () => {
      const formData1 = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "1",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
        "additional-info": "Test description",
      };
      const result1 = validateGeneralQuestions(formData1);
      expect(result1.errors[GENERAL_QUESTION_KEYS[4]]).toBeUndefined();

      const formData2 = {
        ...formData1,
        [GENERAL_QUESTION_KEYS[4]]: ["Professional", "Friendly"],
      };
      const result2 = validateGeneralQuestions(formData2);
      expect(result2.errors[GENERAL_QUESTION_KEYS[4]]).toBeUndefined();
    });
  });

  describe("additional-info validation", () => {
    it("should return error if additional-info is missing", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "1",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
      };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors["additional-info"]).toBe(
        "Please provide a personal description to help us find the most relevant jobs for you."
      );
    });

    it("should return error if additional-info is empty string", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "1",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
        "additional-info": "",
      };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors["additional-info"]).toBeDefined();
    });

    it("should return error if additional-info is only whitespace", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "1",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
        "additional-info": "   ",
      };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(result.errors["additional-info"]).toBeDefined();
    });

    it("should pass validation for valid additional-info", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "1",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional"],
        "additional-info":
          "I am a software developer with 5 years of experience.",
      };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(true);
      expect(result.errors["additional-info"]).toBeUndefined();
    });
  });

  describe("complete form validation", () => {
    it("should return isValid=true for complete valid form", () => {
      const formData = {
        [GENERAL_QUESTION_KEYS[0]]: ["Expert-level"],
        [GENERAL_QUESTION_KEYS[1]]: ["Duunitori", "Jobly"],
        [GENERAL_QUESTION_KEYS[2]]: "Yes",
        [GENERAL_QUESTION_KEYS[3]]: "5",
        [GENERAL_QUESTION_KEYS[4]]: ["Professional", "Friendly"],
        "additional-info":
          "I am a software developer with experience in React and Node.js.",
      };
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(true);
      expect(Object.keys(result.errors).length).toBe(0);
    });

    it("should return all errors for completely empty form", () => {
      const formData = {};
      const result = validateGeneralQuestions(formData);
      expect(result.isValid).toBe(false);
      expect(Object.keys(result.errors).length).toBe(6); // 5 general questions + additional-info
    });
  });
});
