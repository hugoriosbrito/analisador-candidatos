import {describe,expect,it} from "vitest"; import {verdictLabel} from "./verdict";
describe("verdictLabel",()=>{it("traduz os vereditos editoriais",()=>{expect(verdictLabel("NEEDS_CONTEXT")).toBe("Requer contexto")});it("não inventa conclusão para claim sem assessment",()=>{expect(verdictLabel()).toBe("Em análise")})})
