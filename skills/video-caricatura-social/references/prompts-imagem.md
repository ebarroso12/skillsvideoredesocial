# Prompts de imagem: caricatura e cenas

Use estes blocos em qualquer gerador de imagem (conector no Claude, ferramenta nativa no Codex/Manus, ou
um gerador externo que o usuário abra). Escreva os prompts em português ou inglês, conforme o gerador
responder melhor; mantenha os traços do personagem sempre idênticos.

## Regras de ouro

1. **Formato 9:16** (ex.: 1080x1920 ou 1536x2752). Peça "vertical, proporção 9:16".
2. **Espaço livre no terço inferior** (legenda) e **canto inferior direito limpo** (marca d'água).
3. **Sem texto na imagem** (letras geradas saem erradas; a legenda é feita pelo script). Inclua "sem texto, sem letras, sem marca d'água".
4. **Mesmo personagem em todas as cenas**: cole a ficha completa em cada prompt e, se o gerador aceitar,
   envie a imagem aprovada da cena 1 como referência.
5. Gere **uma cena de teste** antes do lote.

## 1. Ficha do personagem (preencha uma vez e reutilize)

```
PERSONAGEM: caricatura de [NOME/ARQUÉTIPO], [idade aparente], [tom de pele], [formato do rosto],
cabelo [cor, corte], [barba/bigode], [óculos], expressão base [serena/cansada/esperançosa],
cabeça ligeiramente maior que o corpo (leve exagero simpático), traços expressivos,
figurino [roupa e cores fixas], [acessório marcante].
```

## 2. Bloco de estilo (escolha um e use em todas as cenas)

- **pintura-fantasia** (estilo do Reel de referência): "pintura digital de fantasia, textura de óleo, luz dourada
  suave, nuvens volumosas, paisagem ampla com o personagem pequeno em escala, atmosfera contemplativa e emotiva,
  alto detalhe, cores ricas".
- **caricatura-colorida**: "caricatura digital colorida, traços limpos, sombreado suave, cores vibrantes,
  fundo ilustrado detalhado, acabamento de ilustração profissional".
- **aquarela**: "ilustração em aquarela, pinceladas visíveis, bordas suaves, paleta delicada, papel texturizado".
- **3d-suave**: "personagem 3D estilizado, materiais macios, iluminação de estúdio quente, profundidade de campo rasa".

## 3. Cores e contexto vindos do usuário

Traduza o pedido do usuário em uma linha de paleta e uma de cenário, e repita em todas as cenas:

```
PALETA: [ex.: tons de azul-noite e dourado quente] | CENÁRIO: [ex.: varanda ao entardecer, cidade pequena]
CLIMA: [acolhedor / melancólico com esperança / luminoso]
```

Se o usuário não indicou, derive do tema (solidão → azul-noite com um ponto de luz dourada; esperança →
amanhecer dourado; cansaço → tons terrosos suaves) e diga em uma linha o que escolheu.

## 4. Prompt de cena (modelo)

```
[BLOCO DE ESTILO]. [FICHA DO PERSONAGEM].
CENA: [o que acontece, em uma frase concreta — ex.: sentado na beira de um penhasco sobre um mar de nuvens, olhando o horizonte].
ENQUADRAMENTO: vertical 9:16, personagem no terço superior/central, [plano aberto/médio],
terço inferior da imagem com espaço livre e tranquilo, canto inferior direito sem elementos importantes.
[PALETA/CENÁRIO/CLIMA]. Sem texto, sem letras, sem marca d'água, sem logotipos.
```

Sugestão de sequência para 6–7 cenas (adapte ao roteiro): 1) plano aberto, personagem pequeno, solitário;
2) close na expressão (o "por fora sorrindo"); 3) o peso (objeto ou clima simbólico); 4) uma luz/mão/presença
que se aproxima (acolhimento); 5) mudança de clima, mais luz; 6) o personagem de pé/ao amanhecer; 7) plano
final calmo, espaço central livre.

## 5. Caricatura a partir de foto enviada pelo usuário

Envie a foto como imagem de referência ao gerador (se a ferramenta aceitar) e use:

```
Transforme a pessoa da foto em uma caricatura [BLOCO DE ESTILO]. Preserve os traços marcantes:
[cabelo, barba, óculos, tom de pele, formato do rosto, sorriso]. Leve exagero simpático e respeitoso
(cabeça um pouco maior, expressão acolhedora), sem deformar de modo ofensivo. Corpo de meio
corpo/corpo inteiro com [figurino]. Fundo [CENÁRIO] em [PALETA]. Vertical 9:16, espaço livre
no terço inferior. Sem texto, sem letras, sem marca d'água.
```

Depois de aprovar essa imagem, reutilize-a como referência para as outras cenas (mesmo rosto).
Se o gerador não aceita imagem de referência, descreva os traços com muito detalhe na ficha e gere várias
opções da cena 1; escolha a mais fiel.

## 6. Negativos úteis (quando o gerador aceita)

"texto, letras, números, marca d'água, logotipo, mãos deformadas, dedos extras, olhos assimétricos,
rosto diferente entre cenas, borrado, baixa resolução, corte do rosto".

## 7. Conectores (Claude) — como descobrir

1. Procure ferramentas de geração de imagem já carregadas (nomes com `generate_image`, `image`, `firefly`).
2. Se não houver, use `SearchMcpRegistry` com palavras como "image generation", "design", "firefly" e
   `SuggestConnectors` para o usuário conectar.
3. Antes de gerar em lote, avise se a ferramenta consome créditos do usuário.
4. Se nada estiver disponível, entregue os prompts numerados e peça as imagens (passo 3 do fluxo).

## 8. Dimensões e arquivos

Salve como `cenas/cena_01.png`, `cena_02.png`... na pasta do projeto. Qualquer tamanho serve; imagens
com proporção bem diferente de 9:16 recebem fundo desfocado automaticamente (`"ajuste": "blur"`).
Quanto mais perto de 1080x1920 ou maior, melhor o movimento de câmera.
