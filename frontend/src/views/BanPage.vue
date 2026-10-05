<template>
  <div class="ban-page">  
    <div class="ban-page-card">  
      <div class="ban-page-icon">🚫</div>  
      <h1 class="ban-page-title">Аккаунт заблокирован</h1>  
      <p class="ban-page-sub">Ваш аккаунт был заблокирован администрацией сайта.</p>  
      <div v-if="banState && banState.reason" class="ban-page-reason">  
        <div class="ban-page-reason-label">Причина блокировки</div>  
        <div class="ban-page-reason-text">{{ banState.reason }}</div>  
      </div>
      <router-link to="/login" class="btn ban-page-btn">Войти в другой аккаунт</router-link>  
    </div>
  </div>
</template>
<script setup>
import { banState } from '../ban'  
</script>
<style scoped>  
.ban-page {
  min-height: 70vh;  
  display: flex;  
  align-items: center;  
  justify-content: center;  
  padding: 32px 16px;  
}
.ban-page-card {
  background: var(--surface);  
  border-radius: 20px;  
  box-shadow: 0 8px 32px rgba(0,0,0,0.10);  
  padding: 48px 40px 40px;  
  max-width: 460px;  
  width: 100%;  
  text-align: center;  
}
.ban-page-icon {
  font-size: 56px;  
  line-height: 1;  
  margin-bottom: 20px;
}
.ban-page-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text);  
  margin: 0 0 10px;
}
.ban-page-sub {
  color: var(--muted);  
  font-size: 15px;
  margin: 0 0 24px;
}
.ban-page-reason {
  background: #fee2e2;  
  border: 1px solid #fca5a5;  
  border-radius: 12px;
  padding: 14px 18px;
  margin-bottom: 20px;
  text-align: left;  
}
[data-theme="dark"] .ban-page-reason {  
  background: #2d1b1b;  
  border-color: #7f1d1d;  
}
.ban-page-reason-label {
  font-size: 11px;  
  font-weight: 600;
  text-transform: uppercase;  
  letter-spacing: 0.06em;  
  color: #dc2626;  
  margin-bottom: 6px;
}
.ban-page-reason-text {
  font-size: 14px;
  color: var(--text);
  line-height: 1.5;  
}
.ban-page-btn {
  display: inline-block;  
  text-decoration: none;  
}
</style>