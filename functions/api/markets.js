const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff'}});

function errorMessage(status,apiMessage){
  const suffix=apiMessage?` Detalhe: ${apiMessage}`:'';
  if(status===400)return `CoinGecko retornou HTTP 400 (requisição inválida).${suffix}`;
  if(status===401)return `CoinGecko retornou HTTP 401 (chave de API ausente ou inválida). Verifique a chave Demo.${suffix}`;
  if(status===403)return `CoinGecko retornou HTTP 403 (acesso bloqueado/negado pelo servidor da CoinGecko).${suffix}`;
  if(status===408)return `CoinGecko retornou HTTP 408 (tempo limite da requisição). Tente novamente.${suffix}`;
  if(status===429)return `CoinGecko retornou HTTP 429 (limite de requisições atingido). Aguarde a tentativa automática ou informe uma chave Demo.${suffix}`;
  if(status===500)return `CoinGecko retornou HTTP 500 (erro interno). Tente novamente mais tarde.${suffix}`;
  if(status===503)return `CoinGecko retornou HTTP 503 (serviço temporariamente indisponível).${suffix}`;
  return `CoinGecko recusou a consulta (HTTP ${status}).${suffix}`;
}

export async function onRequestGet(context){
  try{
    const url=new URL(context.request.url);
    const currency=(url.searchParams.get('currency')||'brl').toLowerCase();
    const page=Math.max(1,Math.min(80,Number(url.searchParams.get('page')||1)));
    const perPage=Math.max(1,Math.min(250,Number(url.searchParams.get('per_page')||250)));
    if(!['brl','usd','eur'].includes(currency))return json({error:'Moeda inválida.'},400);

    const endpoint=new URL('https://api.coingecko.com/api/v3/coins/markets');
    endpoint.searchParams.set('vs_currency',currency);
    endpoint.searchParams.set('order','market_cap_desc');
    endpoint.searchParams.set('per_page',String(perPage));
    endpoint.searchParams.set('page',String(page));
    endpoint.searchParams.set('sparkline','false');
    endpoint.searchParams.set('price_change_percentage','24h');

    const supplied=context.request.headers.get('X-CoinGecko-Key');
    const secret=context.env.COINGECKO_API_KEY;
    const headers={accept:'application/json','user-agent':'CryptoJSON-Studio/1.0'};
    const key=supplied||secret;
    if(key)headers['x-cg-demo-api-key']=key;

    const response=await fetch(endpoint,{headers});
    if(!response.ok){
      let apiMessage='';
      try{
        const raw=await response.text();
        if(raw){
          try{
            const parsed=JSON.parse(raw);
            apiMessage=String(parsed.error||parsed.message||parsed.status?.error_message||'').slice(0,300);
          }catch{
            apiMessage=raw.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim().slice(0,300);
          }
        }
      }catch{}
      console.error(JSON.stringify({event:'coingecko_upstream_error',status:response.status,page,currency,perPage,hasApiKey:Boolean(key),apiMessage}));
      return json({error:errorMessage(response.status,apiMessage),status:response.status,upstream:'CoinGecko'},response.status);
    }

    return new Response(response.body,{status:200,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff'}});
  }catch(error){
    console.error(JSON.stringify({event:'coingecko_proxy_error',message:error instanceof Error?error.message:String(error)}));
    return json({error:'Falha temporária ao consultar os dados de mercado.',status:502},502);
  }
}

export function onRequestOptions(){return new Response(null,{status:204,headers:{allow:'GET, OPTIONS'}})}
