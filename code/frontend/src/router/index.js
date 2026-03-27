import { createRouter, createWebHistory } from 'vue-router'

import ScheduleView from '../views/ScheduleView.vue'
import ContactsView from '../views/ContactsView.vue'
import RulesView from '../views/RulesView.vue'
import TemplatesView from '../views/TemplatesView.vue'
import SettingsView from '../views/SettingsView.vue'
import LogsView from '../views/LogsView.vue'
import ShiftChangesView from '../views/ShiftChangesView.vue'

const routes = [
  { path: '/', redirect: '/schedule' },
  { path: '/schedule', component: ScheduleView },
  { path: '/contacts', component: ContactsView },
  { path: '/rules', component: RulesView },
  { path: '/templates', component: TemplatesView },
  { path: '/settings', component: SettingsView },
  { path: '/logs', component: LogsView },
  { path: '/shift-changes', component: ShiftChangesView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
