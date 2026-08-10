export const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api/v1";
export async function getJson<T>(path:string):Promise<T>{try{const r=await fetch(`${API}${path}`,{next:{revalidate:30}});if(!r.ok)throw new Error(String(r.status));return r.json()}catch{return [] as T}}
