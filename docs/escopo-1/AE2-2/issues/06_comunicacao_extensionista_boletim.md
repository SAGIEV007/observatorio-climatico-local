# Issue 06: Módulo de Comunicação Extensionista, Boletins Agronômicos e Acessibilidade

**Status:** Aberta / Planejada  
**Prioridade:** Média  
**Módulo:** Extensão Universitária & Comunicação  
**Responsável Técnico:** Fernando da Conceição Cordeiro Filho  
**Labels:** `extensao`, `comunicacao`, `relatorio`, `comunidade`, `escopo-1`

---

## 1. Contexto e Motivação
Como projeto integrador extensionista universitário, a solução não deve apenas processar dados, mas devolver conhecimento aplicável e seguro à comunidade de pequenos agricultores familiares da região de Marília-SP. A linguagem técnica dos modelos meteorológicos deve ser traduzida para termos práticos do cotidiano agrícola, prevenindo interpretações incorretas e garantindo rigor ético sob a LGPD.

## 2. Escopo Técnico
- Desenvolver modelo de **Boletim Semanal Agroclimático** (formato PDF/HTML de 1 página) sintetizando os indicadores-chave calculados pela `Consulta 4` de `consultas.sql`.
- Implementar diretrizes de linguagem desmistificada:
  - Substituir siglas meteorológicas herméticas (`CDD`, `TXge30`, `R10mm`) por expressões compreensíveis: *"Dias Seguidos Sem Chuva"*, *"Dias com Calor Intenso (Acima de 30 °C)"*, *"Chuva Forte Acumulada"*.
  - Incluir ícones visuais e esquemas de cores de tráfego (verde = condições favoráveis; amarelo = alerta hídrico/térmico; azul = chuva acumulada expressiva).
- Estruturar canal de devolutiva e feedback da comunidade:
  - Roteiro de escuta qualificada para aplicação junto a pequenos produtores rurais e técnicos da Casa da Agricultura (CATI/CDRS).
  - Mecanismo seguro de coleta de relatos orais e fotografias de lavoura com termo de consentimento prévio e anonimização total, em estrita conformidade com a Lei Geral de Proteção de Dados Pessoais (LGPD — Lei 13.709/2018).
  - Garantir que a pasta `dados/comunidade/` permaneça ignorada no controle de versão (`.gitignore`).
- Redigir cartilha de salvaguarda agronômica:
  - Deixar explícito que os dados refletem estimativas de grade de reanálise (~4,4 km de distância) e não substituem pluviômetros de propriedade.
  - Alerta enfático: dados históricos descrevem o passado recente e **não configuram previsão do tempo para os próximos dias**.
  - Orientação obrigatória para validação de decisões de adubação, pulverização e plantio com agrônomos e assistência técnica habilitada.

## 3. Critérios de Aceitação (Definition of Done)
- [ ] Template de Boletim Agroclimático Semanal gerado e validado em PDF/Markdown.
- [ ] Guia de interpretação em linguagem popular anexo à documentação do projeto.
- [ ] Política de privacidade e conformidade com a LGPD formalizada no repositório.
- [ ] Seção de limites e salvaguardas validada tecnicamente para evitar conclusões precipitadas por parte dos produtores.
- [ ] Mecanismo de exportação rápida de relatórios no dashboard Streamlit (download em CSV e PDF).
