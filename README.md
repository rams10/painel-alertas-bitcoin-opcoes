# Painel de alertas — Bitcoin, opções e swing trade

Painel estático publicado pelo GitHub Pages. Os cálculos e sinais continuam no navegador; as cotações OHLC são atualizadas pelo GitHub Actions e publicadas em `data/market-data.json`.

## Atualização de cotações

- Ações B3: dias úteis, às 21h40 (horário de Brasília).
- Bitcoin: diariamente, às 21h15 (horário de Brasília), após a virada UTC usada pela série diária da Alpha Vantage.
- As ações são consultadas pelo formato `TICKER.SA`.
- Cada resposta traz a janela compacta mais recente; o script mescla datas novas e revisa candles repetidos sem apagar o histórico já acumulado.
- Falhas individuais ficam registradas em `asset_status`; dados anteriores são mantidos.

## Configuração inicial

1. Solicite uma chave pessoal da Alpha Vantage em https://www.alphavantage.co/support/#api-key.
2. No repositório, abra **Settings → Secrets and variables → Actions → New repository secret**.
3. Nome do secret: `ALPHA_VANTAGE_API_KEY`. Valor: sua chave. Não coloque a chave em arquivos do repositório nem no HTML.
4. Em **Settings → Pages**, selecione **GitHub Actions** como fonte de publicação.
5. Em **Actions**, execute **Atualizar dados e publicar painel** com `all` para testar as consultas e publicar os primeiros dados.

O fluxo automático usa até 17 consultas por dia útil para as ações e uma consulta diária para o Bitcoin (18 no total em dias úteis), dentro da franquia padrão documentada de 25 requisições/dia. A Alpha Vantage pode alterar limites e disponibilidade por símbolo.

## Observações

- A Alpha Vantage `TIME_SERIES_DAILY` retorna OHLC diário bruto (não ajustado por dividendos/desdobramentos). Isso preserva a mesma família de dados usada originalmente pelo painel.
- O histórico inicial embutido no `index.html` é mantido. O arquivo remoto complementa esse histórico com candles recentes.
- O histórico local importado por CSV e as posições de swing ficam no `localStorage` do navegador; não são sincronizados entre dispositivos.
- O site e seus arquivos serão públicos porque este repositório usa GitHub Pages gratuito.
- Material de apoio pessoal; não constitui recomendação de investimento.
