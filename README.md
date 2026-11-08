# Sala — índice completo para GitHub Pages

Publicado em https://marlonambrosio.github.io/cinema-tablet/

Correção: `players.js` acrescenta players públicos para os 36 primeiros filmes, preservando os 16 anteriores. A interface começa com o filtro **Com player importado** (52 filmes). O índice completo continua disponível em Disponibilidade. Players importados não equivalem a reprodução validada. `catalogo.json` e `servidores.csv` continuam com os 16 originais; os 36 adicionais ficam no arquivo complementar `players.js`. Inclua esse arquivo ao publicar.

Importação dos 89 sitemaps públicos de conteúdo do site consultado em 8 de novembro de 2026. Foram removidas entradas duplicadas e páginas de índice.

| Tipo | Registros |
|---|---:|
| Filmes | 14.631 |
| Séries | 2.932 |
| Episódios | 64.186 |
| Temporadas | 5.294 |
| Total | 87.043 |

## O que está completo e o que não está

O índice contém todos os registros encontrados nos sitemaps públicos consultados, incluindo endereço original e capa quando fornecida. Isso não comprova que cada página ou vídeo esteja disponível.

**Somente os 16 filmes da amostra anterior têm players extraídos (89 endereços).** Os demais registros oferecem acesso à página de origem e são identificados assim na interface. Não foram inventados endereços de players. Os servidores são páginas de incorporação; não são arquivos MP4/M3U8.

Os sitemaps não fornecem nomes oficiais. Para 87.027 registros, o nome exibido é uma etiqueta derivada do endereço da página: pode conter abreviações, números ou marcadores do site. Os 16 títulos previamente consultados preservam seus nomes extraídos da página.

`cobertura.json` registra as contagens e a cobertura de players. `catalogo.json` contém os registros completos. `servidores.csv` contém somente os players realmente encontrados.

## Publicar no GitHub Pages

1. Extraia o ZIP e envie os arquivos para a raiz de um repositório GitHub. Inclua obrigatoriamente a pasta **dados**.
2. Abra **Settings → Pages → Build and deployment → Deploy from a branch**.
3. Selecione a branch `main` e a pasta `/(root)`; salve.
4. Abra no tablet o endereço HTTPS informado pelo GitHub.

Arquivos necessários ao site: `index.html`, `estilo.css`, `app.js`, `catalogo.js`, `.nojekyll` e todos os arquivos em `dados/`. Os demais arquivos são documentação, dados para exportação e ferramentas de atualização. Não há chaves ou senhas. A interface foi publicada no GitHub Pages.

## Desempenho no tablet

- Interface sem bibliotecas de execução, em JavaScript ES5.
- Somente 36 cartões são inseridos por página.
- Séries, temporadas e episódios são carregados ao selecionar a categoria. Os episódios formam a categoria mais volumosa; a primeira abertura pode demorar.
- Busca com atraso de 200 ms e comparação sem acentos quando suportada pelo navegador.
- Capas têm carregamento adiado quando o navegador oferece esse recurso.
- Favoritos e último título ficam apenas no navegador local.

## Atualizar o índice completo

Com Python 3 no computador, na pasta extraída:

```text
python scripts/importar_indice_completo.py
```

O script consulta o sitemap público, faz no máximo três consultas simultâneas e espaça os inícios das requisições em pelo menos 450 ms. O cache em `.cache-indice/` vale por uma hora e permite retomar falhas. Não envie essa pasta ao GitHub. Se um sitemap falhar, o catálogo anterior é preservado e os erros são listados em `falhas-importacao.json`. Execute novamente para tentar concluir.

A importação mantém os players já conhecidos, mas não percorre individualmente as 87 mil páginas para obter players novos. O script `atualizar_catalogo.py` é o importador da amostra original e também fornece funções ao importador completo; não o execute para substituir este catálogo por uma amostra.

## Publicidade e disponibilidade

A interface não inclui os scripts de publicidade do catálogo original. O sandbox do iframe restringe pop-ups, downloads e redirecionamentos da página inteira. Publicidade exibida dentro de players externos **não é removida**. Não é possível prometer uma sessão sem anúncios.

Players podem recusar incorporação, exigir um Referer ou um navegador mais recente, ou depender de recursos bloqueados. Não enfraqueça o isolamento para corrigir isso. Capas, páginas de origem e players podem registrar seus próprios acessos; esta interface não adiciona analytics.

Não há download de vídeos, login, resolução de CAPTCHAs ou remoção de proteções. Um endereço público não comprova autorização para distribuir o conteúdo; use os materiais que você tenha direito de acessar e incorporar.

## Validação

Contagens, duplicatas, sintaxe JavaScript e integridade do ZIP foram verificadas. Um teste de DOM conferiu busca, paginação, favoritos, carregamento das quatro categorias e criação/remoção do iframe com sandbox. Não substitui teste visual nem reprodução real. Os players não foram validados no SM-T561M; a prévia visual ficou indisponível no navegador desta sessão.

## Importação incremental e limitações atuais

`python scripts/importar_players.py --limite 100` consulta até 100 páginas, alternando filmes, séries e episódios. `--todos` percorre o índice até concluir ou encontrar bloqueios. Retoma pelo checkpoint local `.progresso-players.json`, preserva os endereços anteriores em `players.js` e registra `relatorio-importacao.json`. Uma execução posterior ignora páginas já consultadas com sucesso. Para reexaminar páginas sem player após mudanças no site, remova somente as respectivas entradas desse checkpoint local. Erros HTTP 401/403/429 e desafios anti-bot interrompem a execução, sem contorno. Não há execução agendada nem atualização automática do GitHub.

Na última tentativa, a origem respondeu HTTP 403 antes de importar qualquer título novo. O navegador mostrou verificação Cloudflare. Por isso, permanecem 52 filmes com links de player (16 originais e 36 complementares), sem confirmação geral de reprodução. Não foram importados players de séries nesta execução.

A interface aplica os dados complementares também às categorias carregadas sob demanda. Séries e temporadas oferecem navegação para episódios cujos endereços indexados seguem exatamente o mesmo identificador e numeração. Essa associação é derivada dos slugs do índice, não de metadados de relacionamento verificados. A lista usa os URLs existentes, sem inventar episódios ou players. Selecionar Séries ou Temporadas mostra o índice completo dessa categoria, incluindo itens sem player.

`status-players.js` registra apenas os cinco endereços do filme Rômulo e Remo testados no navegador, sem extrapolar o resultado a outros filmes. Nenhum foi confirmado reproduzindo: houve acesso negado, 404, recusa ao isolamento e controles em 0:00. O botão de abertura externa é opcional e pode expor anúncios e pop-ups dos servidores externos; não remove o isolamento do player incorporado.

Inclua `players.js` e `status-players.js` na raiz ao publicar. A confirmação de resposta HTTP ou a exibição de controles não representa reprodução validada.
