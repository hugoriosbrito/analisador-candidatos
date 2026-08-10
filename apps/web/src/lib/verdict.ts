export const verdictLabels: Record<string,string>={SUPPORTED:"Sustentada",MOSTLY_SUPPORTED:"Majoritariamente sustentada",NEEDS_CONTEXT:"Requer contexto",UNSUPPORTED:"Não sustentada",FALSE:"Falsa",INCONCLUSIVE:"Inconclusiva",NOT_CHECKABLE:"Não verificável"};
export function verdictLabel(v?:string){return v?verdictLabels[v]??v:"Em análise"}
