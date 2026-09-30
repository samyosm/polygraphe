import type { components } from "./schema";

/** Types generated from the backend's OpenAPI schema (`pnpm api:types`). */
type Schemas = components["schemas"];

export type Trial = Schemas["TrialOut"];
export type TrialStatus = Schemas["TrialStatus"];
export type TrialDetails = Schemas["TrialDetails"];
export type Subject = Schemas["SubjectSchema"];
export type Sex = Schemas["Sex"];
export type Device = Schemas["DeviceOut"];
export type Measurement = Schemas["MeasurementOut"];
export type Stage = Schemas["Stage"];
