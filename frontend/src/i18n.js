import { ref } from 'vue'  

export const lang = ref(localStorage.getItem('lang') || 'ru')  

export function setLang(l) {  
  lang.value = l  
  localStorage.setItem('lang', l)  
}

const en = {  
  'Главная': 'Home',
  'Коллекции': 'Collections',
  'Создать': 'Create',
  'Сообщения': 'Messages',
  'Уведомления': 'Notifications',
  'Профиль': 'Profile',
  'Выйти': 'Sign Out',
  'Модерация': 'Moderation',
  'Поиск': 'Search',
  'Войти': 'Sign In',
  'Регистрация': 'Sign Up',
  'Подписаться': 'Subscribe',
  'Отписаться': 'Unsubscribe',
  'Изменить': 'Edit',
  'Удалить': 'Delete',
  'Сохранить': 'Save',
  'Сохранено': 'Saved',
  'Отмена': 'Cancel',
  'Отправить': 'Send',
  'Пожаловаться': 'Report',
  'Заблокировать': 'Block',
  'Разблокировать': 'Unblock',
  'Поделиться': 'Share',
  'Скопировано': 'Copied',
  'Загрузка...': 'Loading...',
  'Репост': 'Repost',
  'Репостнуто': 'Reposted',
  'Быстрый репост': 'Quick Repost',
  'Репост с комментарием': 'Quote Repost',
  'Отменить репост': 'Undo Repost',
  'Комментарии': 'Comments',
  'Напишите комментарий...': 'Write a comment...',
  'Ответить': 'Reply',
  'Отправить на модерацию': 'Submit for Review',
  'Уведомлений нет': 'No notifications',
  'Очистить все': 'Clear all',
  'Нет сообщений': 'No messages',
  'Сообщение...': 'Message...',
  'Изменить профиль': 'Edit Profile',
  'Сменить пароль': 'Change Password',
  'Приватность': 'Privacy',
  'Приватный аккаунт': 'Private Account',
  'Заблокированные пользователи': 'Blocked Users',
  'Удаление аккаунта': 'Delete Account',
  'Все': 'All',
  'Подписки': 'Following',
  'Новые': 'New',
  'Популярные': 'Popular',
  'Созданные': 'Created',
  'Сохранённые': 'Saved',
  'Репосты': 'Reposts',
  'Понравившиеся': 'Liked',
  'Возвращённые': 'Returned',
  'Подписчики': 'Followers',
  'Черновики': 'Drafts',
  'Фото': 'Photo',
  'Видео': 'Video',
  'Скачать': 'Download',
  'Нет коллекций': 'No collections',
  'Тёмная тема': 'Dark mode',
  'Светлая тема': 'Light mode',
}

export function t(key) {  
  if (lang.value === 'ru') return key  
  return en[key] ?? key  
}
