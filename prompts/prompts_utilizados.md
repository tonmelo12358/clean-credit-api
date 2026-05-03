# Registro de Prompts: Construção da CleanCredit API

## 1. Definição da Arquitetura e Escopo do MVP
**Objetivo**: Estabelecer a estrutura de pastas e a arquitetura "Clean" para o projeto Python.

> "Atue como um Arquiteto de Software Sênior. Preciso criar um MVP de uma API de crédito chamada CleanCredit API. O projeto deve usar Python e FastAPI. Estruture o repositório seguindo os princípios de Clean Architecture, separando as camadas de Domínio, Adaptores e Serviços. Crie o esqueleto das pastas e o arquivo inicial de rotas."


## 2. Modelagem da Entidade de Proposta (Proposal)
**Objetivo**: Definir o contrato de dados e validações da proposta de crédito.

> "Crie o modelo de dados Proposal utilizando Pydantic. A proposta deve conter: CPF, Nome Completo, Renda Mensal e Valor Solicitado. Adicione validações básicas para garantir que o CPF seja uma string e os valores financeiros sejam decimais positivos."


## 3. Implementação do Motor de Regras Local (Fallback)
**Objetivo**: Criar a lógica de decisão local para quando a IA estiver indisponível.

> "Implemente uma classe de serviço que realize uma análise de crédito baseada em regras simples (Hard Rules). Se a renda for superior a um determinado valor e o solicitado for menor que uma porcentagem da renda, retorne aprovação. Este será o nosso Stub/Fallback local."


## 4. Integração com a API do Google Gemini
**Objetivo**: Criar o adaptador para consumo de IA generativa para scoring de crédito.

> "Desenvolva um adaptador chamado GeminiProvider que consuma a API do Google Gemini via REST. O adaptador deve enviar os dados da proposta e solicitar um score de 0 a 1 e uma justificativa técnica. Utilize a biblioteca httpx para chamadas assíncronas e configure o modelo gemini-1.5-flash."  


## 5. Orquestração de Serviços e Resiliência
**Objetivo**: Criar o serviço que tenta a IA e desvia para o motor local em caso de falha.

> "Crie o ProposalService que orquestra a análise. Ele deve tentar obter o score via GeminiProvider. Caso ocorra um erro de timeout ou rede (400/500), ele deve acionar automaticamente o motor de regras local para garantir que o usuário receba uma resposta. Aplique o padrão de inversão de dependência."  


## 6. Automação de Ambiente e Setup (Makefile)
**Objetivo**: Facilitar a reprodutibilidade em máquinas limpas através de comandos simplificados.

> "Crie um arquivo Makefile para automatizar o projeto. Inclua comandos para: instalar dependências (install), rodar o servidor (run), executar testes unitários (test) e realizar a verificação de estilo com ruff (lint)."  


## 7. Roteiro para Apresentação Técnica
**Objetivo**: Estruturar a demonstração do MVP para stakeholders técnicos.

> "Crie um roteiro de apresentação em Markdown para um MVP de 5 minutos. O objetivo é mostrar o terminal, os comandos de execução e o fluxo direto da API, sem foco em marketing."


## 8. Checklist Final de Submissão
**Objetivo**: Validar todos os itens de segurança, versionamento e documentação antes da entrega.

> "Verifique o repositório contra o checklist de submissão: repositório público, histórico de commits consistente, ausência de credenciais expostas no código, presença de arquivo .env.example e criação da tag de versão v1.0.0."