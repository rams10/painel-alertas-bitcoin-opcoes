# Painel de Bitcoin e opções

Aplicativo independente para acompanhar os guias de Bitcoin e os sinais de venda de puts e calls em ações. O programa de swing trade agora tem página, histórico, rotina e chave de API separados em `/swing/`.

## Programa de Bitcoin e opções

- Interface: `index.html`.
- Dados exclusivos: `data/market-data.json`.
- Atualizador: `scripts/update_market_data.py`.
- Universo de ações para opções: SBSP3, BBSE3, ISAE4, EGIE3, PETR4, VALE3, BBAS3, BBDC4, ITUB4, ITSA4, AXIA3.
- Bitcoin é consultado separadamente pela série diária digital.
- Secret do GitHub: `ALPHA_VANTAGE_API_KEY`.
- Coletas: Bitcoin diariamente às 21h15 e ações em dias úteis às 21h40 (horário de Recife).

## Programa independente de swing trade

- Painel: `swing/index.html`.
- Histórico base local do app: `swing/data/seed.json`.
- Cache de mercado: `swing/data/market-data.json`.
- Atualizador separado: `scripts/update_swing_market_data.py`.
- Universo: WEGE3, SUZB3, ITUB4, B3SA3, AXIA3, VALE3, PRIO3, BPAC11, PETR4, GGBR4, BBAS3.
- Secret dedicado recomendado: `ALPHA_VANTAGE_SWING_API_KEY`. Enquanto ele não for criado, o fluxo usa a chave principal como fallback; criar o segundo secret mantém cotas e falhas isoladas.
- Coleta automática em dias úteis às 22h00 (horário de Recife), após o programa de opções.

## Chaves da Alpha Vantage

No GitHub, abra **Settings → Secrets and variables → Actions**. Mantenha `ALPHA_VANTAGE_API_KEY` para opções/Bitcoin. Para separar a credencial do swing trade, crie também `ALPHA_VANTAGE_SWING_API_KEY` com a nova chave e salve diretamente como Secret. Enquanto esse segundo secret não existir, o atualizador de swing usa a chave principal como fallback. Nunca coloque as chaves em arquivos ou no HTML.

O fluxo faz até 12 chamadas/dia para Bitcoin e opções (11 ações + 1 Bitcoin nos dias úteis, 1 para Bitcoin no fim de semana) e até 11 chamadas/dia para swing trade. Se ambos usarem a mesma chave, são até 23 chamadas nos dias úteis. A Alpha Vantage informa limite padrão de 25 requisições/dia para o serviço gratuito; portanto, a margem com uma única chave é pequena. A página pública do provedor não esclarece se duas chaves emitidas na mesma conta recebem cotas independentes; a segunda chave separa as credenciais no código, mas confirme com o provedor a separação efetiva de cota.

## Publicação

O GitHub Pages publica os dois programas no mesmo domínio, mas com arquivos, caches, atualizadores e segredos independentes. O deploy é serializado para não disputar a publicação do site.

## Observações

- Ações usam `TIME_SERIES_DAILY` para tickers no formato `.SA` e candles OHLC não ajustados.
- As rotinas guardam os candles anteriores e mesclam/revisam datas repetidas.
- O histórico importado por CSV e as posições de swing ficam somente no navegador.
- O site e seus arquivos são públicos por usar GitHub Pages.
- Material de apoio pessoal, não recomendação de investimento.
