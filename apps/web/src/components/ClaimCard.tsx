import Link from "next/link"; import {verdictLabel} from "@/lib/verdict";
export function ClaimCard({c}:{c:any}){return <Link href={`/checagens/${c.id}`} className="card claim"><span className="badge">{verdictLabel(c.assessment?.verdict)}</span><q>{c.text}</q><span className="muted">{c.topic||"Sem tópico"} · Ver evidências →</span></Link>}
