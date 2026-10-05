import { createRouter, createWebHistory } from 'vue-router'  
import { auth } from './auth'  


import Feed from './views/Feed.vue'  
import Landing from './views/Landing.vue'  
import Login from './views/Login.vue'  
import Register from './views/Register.vue'  
import CreatePost from './views/CreatePost.vue'  
import PostDetail from './views/PostDetail.vue'  
import Profile from './views/Profile.vue'  
import Collections from './views/Collections.vue'  
import CollectionDetail from './views/CollectionDetail.vue'  
import Inbox from './views/Inbox.vue'  
import ChatRoom from './views/ChatRoom.vue'  
import EditProfile from './views/EditProfile.vue'  
import TagFeed from './views/TagFeed.vue'  
import Notifications from './views/Notifications.vue'  
import Search from './views/Search.vue'  
import Moderation from './views/Moderation.vue'  
import BanPage from './views/BanPage.vue'  

const routes = [  
  { path: '/', component: Feed },  
  { path: '/welcome', component: Landing },  
  { path: '/login', component: Login },  
  { path: '/register', component: Register },  
  { path: '/create', component: CreatePost, meta: { requiresAuth: true } },  
  { path: '/post/:id', component: PostDetail, meta: { requiresAuth: true } },  
  { path: '/user/:username', component: Profile, meta: { requiresAuth: true } },  
  { path: '/collections', component: Collections, meta: { requiresAuth: true } },  
  { path: '/collection/:id', component: CollectionDetail, meta: { requiresAuth: true } },  
  { path: '/messages', component: Inbox, meta: { requiresAuth: true } },  
  { path: '/messages/:username', component: ChatRoom, meta: { requiresAuth: true } },  
  { path: '/settings', component: EditProfile, meta: { requiresAuth: true } },  
  { path: '/tag/:slug', component: TagFeed, meta: { requiresAuth: true } },  
  { path: '/notifications', component: Notifications, meta: { requiresAuth: true } },  
  { path: '/search', component: Search, meta: { requiresAuth: true } },  
  { path: '/moderation', component: Moderation, meta: { requiresAuth: true } },  
  { path: '/banned', component: BanPage },  
]

const router = createRouter({  
  history: createWebHistory(),  
  routes,  
})

router.beforeEach((to) => {  
  if (to.path === '/banned') return  
  if (to.meta.requiresAuth && !auth.isAuthenticated()) return '/welcome'  
  if (to.path === '/' && !auth.isAuthenticated()) return '/welcome'  
  if (to.path === '/welcome' && auth.isAuthenticated()) return '/'  
  
})

export default router  
