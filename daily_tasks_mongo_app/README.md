# Gestor de Tarefas Diário - Python + MongoDB

Aplicativo completo em Python com Flask e MongoDB para registar tarefas diárias.

## Funções
- adicionar tarefas
- marcar como concluída
- eliminar tarefa
- filtrar por estado e categoria
- calcular tempo estimado pendente
- interface responsiva para celular
- instalável no celular como app web (PWA)
- pronto para Railway

## Como executar localmente
1. Criar ambiente virtual
2. Instalar dependências
3. Criar `.env`
4. Executar `python app.py`

## Variáveis de ambiente
Veja `.env.example`

## Deploy no Railway
- subir para GitHub
- criar projeto no Railway
- deploy do repositório
- adicionar MongoDB no mesmo projeto
- adicionar `MONGO_DATABASE=daily_tasks_db`
