function handleRefresh() {
  globalThis.location.reload();
}

const todoModal = document.getElementById('todo-modal');
const openTodoModalBtn = document.getElementById('open-todo-modal');
const closeTodoModalBtn = document.getElementById('close-todo-modal');
const cancelTodoModalBtn = document.getElementById('cancel-todo-modal');
const todoForm = document.getElementById('todo-form');
const todoTableBody = document.getElementById('todo-table-body');
const todoEmptyState = document.getElementById('todo-empty-state');
const todoCount = document.getElementById('todo-count');
const todoFormMessage = document.getElementById('todo-form-message');

function setModalVisible(visible) {
  if (!todoModal) return;
  todoModal.classList.toggle('hidden', !visible);
  todoModal.setAttribute('aria-hidden', String(!visible));

  if (visible) {
    const titleInput = document.getElementById('todo-title');
    if (titleInput) {
      titleInput.focus();
    }
  }
}

function renderTodos(todos) {
  if (!todoTableBody || !todoCount) return;

  todoCount.textContent = String(todos.length);

  if (!todos.length) {
    todoTableBody.innerHTML = '';
    if (todoEmptyState) {
      todoEmptyState.hidden = false;
    }
    return;
  }

  if (todoEmptyState) {
    todoEmptyState.hidden = true;
  }
  todoTableBody.innerHTML = todos
    .map((todo) => `
      <tr>
        <td class="todo-title-cell">${escapeHtml(todo.title)}</td>
        <td class="todo-desc-cell">${escapeHtml(todo.description || '—')}</td>
        <td class="todo-date-cell">${escapeHtml(todo.created_at)}</td>
        <td><button class="todo-delete-btn" type="button" data-delete-id="${todo.id}">Supprimer</button></td>
      </tr>
    `)
    .join('');
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

async function loadTodos() {
  try {
    const response = await fetch('/api/todos');
    if (!response.ok) throw new Error('Impossible de charger les TODO');
    const data = await response.json();
    renderTodos(data.todos || []);
  } catch (error) {
    if (todoFormMessage) {
      todoFormMessage.textContent = error.message;
    }
  }
}

async function createTodo(event) {
  event.preventDefault();

  if (!todoFormMessage) return;

  const formData = new FormData(todoForm);
  const title = String(formData.get('title') || '').trim();
  const description = String(formData.get('description') || '').trim();

  if (!title) {
    todoFormMessage.textContent = 'Le titre est obligatoire.';
    return;
  }

  todoFormMessage.textContent = 'Enregistrement…';

  try {
    const response = await fetch('/api/todos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Impossible d’ajouter la TODO.');
    }

    todoForm.reset();
    todoFormMessage.textContent = 'TODO ajoutée avec succès.';
    setModalVisible(false);
    await loadTodos();
  } catch (error) {
    todoFormMessage.textContent = error.message;
  }
}

async function deleteTodo(todoId) {
  try {
    const response = await fetch(`/api/todos/${todoId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Impossible de supprimer la TODO.');
    await loadTodos();
  } catch (error) {
    if (todoFormMessage) {
      todoFormMessage.textContent = error.message;
    }
  }
}

openTodoModalBtn?.addEventListener('click', () => setModalVisible(true));
closeTodoModalBtn?.addEventListener('click', () => setModalVisible(false));
cancelTodoModalBtn?.addEventListener('click', () => setModalVisible(false));

todoModal?.addEventListener('click', (event) => {
  if (event.target === todoModal) {
    setModalVisible(false);
  }
});

todoForm?.addEventListener('submit', createTodo);

todoTableBody?.addEventListener('click', (event) => {
  const deleteButton = event.target.closest('[data-delete-id]');
  if (deleteButton) {
    deleteTodo(deleteButton.getAttribute('data-delete-id'));
  }
});
