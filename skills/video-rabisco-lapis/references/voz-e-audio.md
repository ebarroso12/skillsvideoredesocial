# Voz e música

A narração dá muita força ao Reel de referência, mas o vídeo funciona também só com legenda + música.
O motor de vídeo aceita os dois arquivos opcionais em `audio.voz` e `audio.musica`.

## Opções de voz (escolha a mais simples disponível)

1. **Voz do próprio usuário** (melhor para confiança e autenticidade): o usuário grava o roteiro no
   celular, em ambiente silencioso, e envia o arquivo (m4a/mp3/wav). Entregue o roteiro limpo para ele ler,
   com as pausas marcadas por "/" entre as cenas.
2. **Voz sintética**: use a ferramenta de voz do ambiente, se houver (conector de texto para fala, serviço que o
   usuário já assina). Não assuma que existe; se não houver, ofereça a opção 1 ou 3. Evite clonar a voz de
   uma pessoa sem consentimento dela.
3. **Sem voz**: só legenda e música. Funciona bem em Reels vistos sem som.

## Como o script usa a voz

- A duração da voz define o tempo total: as cenas se esticam proporcionalmente ao número de palavras de
  cada uma (ou use `cenas[].duracao` em todas para controle total).
- `audio.voz_tail` (padrão 0,4 s) é a respiração depois da última palavra, antes da tela final.
- A tela final (4,5 s) vem **depois** da voz e conta no limite de 60 s: com voz, o áudio deve ter no
  máximo ~55 s.
- Para a legenda acompanhar bem, divida o roteiro em cenas que correspondam às pausas da fala.

## Música

- Instrumental calma, sem letra, volume baixo: o script usa 0,14 com voz e 0,6 sem voz, com fade-in de
  1 s e fade-out de 2 s. Ajuste em `audio.musica_volume`.
- Use só música com direito de uso (biblioteca do Instagram/TikTok para publicar direto na plataforma,
  ou trilha livre/licenciada). Não use faixas comerciais sem licença.

## Sincronia fina (opcional)

Se o ambiente tiver `whisper` ou similar, transcreva a voz e divida o roteiro em cenas nos pontos de
pausa reais; ajuste `cenas[].duracao` com esses tempos. Sem isso, a estimativa por nº de palavras é suficiente.
