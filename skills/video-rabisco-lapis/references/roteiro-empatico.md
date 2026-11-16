# Roteiro e legenda empáticos

O objetivo do vídeo não é vender uma consulta; é fazer a pessoa se sentir **vista**. A consulta entra
como consequência natural do acolhimento, no final, como um convite.

## Orçamento de tempo (vídeo de ~45 s)

| Trecho | Tempo | Função | Palavras |
|---|---|---|---|
| Gancho | 0–4 s | pergunta ou frase que toca a dor em primeira pessoa/segunda pessoa | 10–14 |
| Dor | 4–16 s | nomear o que a pessoa sente e esconde ("por fora… por dentro…") | 28–34 |
| Virada / acolhimento | 16–28 s | "você não está sozinho(a)", validação sem minimizar | 28–32 |
| Perspectiva do médico | 28–38 s | escuta antes de julgar, cuidar da pessoa e não só do sintoma | 22–26 |
| Convite | 38–45 s | convite curto para cuidar de si (a tela final traz os dados) | 12–16 |

Regra de bolso: **2,6 palavras por segundo**. 40 s ≈ 100 palavras. Mais que ~130 palavras não cabe
em 60 s com a tela final de 4,5 s. O script avisa e bloqueia.

## Tom de voz

- Segunda pessoa ("você"), frases curtas, uma ideia por frase. Ritmo de conversa baixa, não de propaganda.
- Valide antes de orientar: reconhecer a dor vem antes de qualquer conselho.
- Palavras concretas ("silêncio pesa", "sorrir por fora"), não jargão clínico.
- Fé e espiritualidade podem aparecer se o perfil/tema pedir, sempre sem substituir o cuidado em saúde
  ("a fé pode dar esperança, mas não precisamos esconder o que sentimos").
- Nunca: promessa de cura, culpa ("você precisa reagir"), minimizar ("é só fase"), diagnóstico, medo,
  urgência artificial, "antes e depois", depoimentos.

## Frases que funcionam como gancho

- "Você já se sentiu sozinho, mesmo tentando ser forte todos os dias?"
- "Quantas vezes você disse 'tô bem' sem estar?"
- "Cansar de ser forte também é humano."
- "Tem dor que não aparece no exame, mas pesa no peito."
- "Você cuida de todo mundo. E de você, quem cuida?"

## Exemplo de roteiro (tema: ansiedade à noite) — ~95 palavras

1. Gancho — "Você já deitou cansado e a cabeça simplesmente não desligou?"
2. Dor — "A casa em silêncio, o corpo parado, e os pensamentos correndo. Durante o dia, você dá conta de tudo. À noite, tudo pesa mais."
3. Virada — "Sabe o que eu quero lhe dizer? Isso tem nome, tem cuidado, e você não precisa passar por isso sozinho."
4. Médico — "Como médico, aprendi que cuidar vai além do sintoma. Cada pessoa tem uma história, e ela merece ser ouvida antes de ser julgada."
5. Convite — "Não espere piorar para pedir ajuda. Você merece descansar de verdade."
(Tela final: "Agende sua consulta…")

## Legenda do post (texto que acompanha o vídeo)

Estrutura (o script acrescenta o bloco de contato e as hashtags a partir do `brand.json`):

1. **Gancho** (a mesma pergunta do vídeo).
2. **Validação da dor** (1–2 frases curtas).
3. **Contraste por fora/por dentro** ou outra imagem concreta.
4. **Virada de esperança** ("você não precisa carregar tudo sozinho").
5. **Voz do médico** (1–2 frases sobre escutar antes de julgar).
6. **Convite** (não espere o sofrimento se tornar insuportável).
7. **Fecho de dignidade** ("Sua saúde merece atenção. Sua história merece respeito.").

Depois vêm, automaticamente: frase de CTA, WhatsApp, endereço, site, nome + CRM e hashtags.

Coloque esse texto em `post.corpo` do `project.json`. Parágrafos curtos, uma linha em branco entre eles.
Se o tema envolver risco de autolesão/suicídio, acrescente ao final do corpo:
"Se você está em sofrimento agora, ligue para o CVV: 188 (24 horas, gratuito). Em emergência, SAMU 192."

## Hashtags

3 a 6 hashtags, sem exagero. Base em `brand.json` (`#DrEdsonBarroso #SaudeMental #SaudeEmocional
#CuidadoHumanizado #FrancaSP`) mais 1–2 do tema (ex.: `#Ansiedade`, `#Acolhimento`). Passe a lista em `post.hashtags`
para substituir a base.

## Variações de frase de CTA

- "Agende sua consulta e dê o primeiro passo para cuidar de você." (padrão)
- "Você não precisa enfrentar isso sozinho. Fale comigo pelo WhatsApp."
- "Cuidar de você começa com uma conversa. Agende sua avaliação."
