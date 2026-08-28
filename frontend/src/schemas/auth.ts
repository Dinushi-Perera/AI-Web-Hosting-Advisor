import { z } from "zod";

const emailSchema = z.string().trim().min(1, "Enter your email address.").regex(/@/, "Email address must include @.").email("Enter a valid email address with a domain.").max(254);

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(8, "Password must be at least 8 characters."),
});

export const registerSchema = z.object({
  fullName: z.string().trim().min(2, "Enter your full name.").max(100),
  email: emailSchema,
  password: z.string().min(8).regex(/[A-Z]/, "Add an uppercase letter.").regex(/[a-z]/, "Add a lowercase letter.").regex(/[0-9]/, "Add a number.").regex(/[^A-Za-z0-9]/, "Add a special character."),
  confirmPassword: z.string(),
}).refine((v) => v.password === v.confirmPassword, { path: ["confirmPassword"], message: "Passwords do not match." });
