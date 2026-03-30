<script setup lang="ts">
import { ref } from 'vue'
import { useWizardStore } from '@/stores/wizard'
import Input from '@/components/ui/Input.vue'
import Label from '@/components/ui/Label.vue'
import Alert from '@/components/ui/Alert.vue'
import { ChevronDown, ChevronRight, Star, KeyRound } from 'lucide-vue-next'

const wizard = useWizardStore()

const guideOpen = ref(false)
const activeMethod = ref<'service_account' | 'oauth2'>('service_account')
</script>

<template>
  <div>
    <div class="mb-6">
      <h2 class="text-xl font-bold text-foreground">{{ $t('wizard.gsc.title') }}</h2>
      <p class="text-muted-foreground mt-1 text-sm">{{ $t('wizard.gsc.subtitle') }}</p>
    </div>

    <!-- Enable toggle -->
    <label class="flex items-center gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all mb-5"
      :class="wizard.form.gsc_enabled ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/30'"
    >
      <input type="checkbox" v-model="wizard.form.gsc_enabled" class="w-4 h-4 accent-primary rounded" />
      <div>
        <p class="font-semibold text-sm text-foreground">{{ $t('wizard.gsc.enableLabel') }}</p>
        <p class="text-xs text-muted-foreground mt-0.5">{{ $t('wizard.gsc.enableSubtitle') }}</p>
      </div>
    </label>

    <div v-if="wizard.form.gsc_enabled" class="space-y-5">

      <!-- ── Collapsible Setup Guide ── -->
      <div class="rounded-xl border border-border overflow-hidden">
        <button
          type="button"
          @click="guideOpen = !guideOpen"
          class="w-full flex items-center justify-between px-4 py-3 bg-muted/50 hover:bg-muted transition-colors text-left"
        >
          <span class="text-sm font-semibold text-foreground flex items-center gap-2">
            <span>📖</span> How to connect Google Search Console
          </span>
          <ChevronDown v-if="guideOpen" class="w-4 h-4 text-muted-foreground" />
          <ChevronRight v-else class="w-4 h-4 text-muted-foreground" />
        </button>

        <div v-if="guideOpen" class="p-4 space-y-4 border-t border-border bg-background">

          <!-- Method picker -->
          <div class="grid grid-cols-2 gap-2">
            <button
              type="button"
              @click="activeMethod = 'service_account'"
              class="flex items-start gap-2 p-3 rounded-lg border text-left text-xs transition-colors"
              :class="activeMethod === 'service_account'
                ? 'border-primary bg-primary/5 text-primary'
                : 'border-border text-muted-foreground hover:border-primary/40'"
            >
              <Star class="w-4 h-4 mt-0.5 shrink-0" />
              <div>
                <p class="font-semibold">Service Account</p>
                <p class="opacity-70 mt-0.5 leading-tight">Recommended — no browser popup, works headlessly</p>
              </div>
            </button>
            <button
              type="button"
              @click="activeMethod = 'oauth2'"
              class="flex items-start gap-2 p-3 rounded-lg border text-left text-xs transition-colors"
              :class="activeMethod === 'oauth2'
                ? 'border-primary bg-primary/5 text-primary'
                : 'border-border text-muted-foreground hover:border-primary/40'"
            >
              <KeyRound class="w-4 h-4 mt-0.5 shrink-0" />
              <div>
                <p class="font-semibold">OAuth 2.0</p>
                <p class="opacity-70 mt-0.5 leading-tight">Opens browser once for consent, then auto-refreshes</p>
              </div>
            </button>
          </div>

          <!-- Service Account steps -->
          <div v-if="activeMethod === 'service_account'" class="space-y-3 text-sm">
            <ol class="space-y-3 list-none">
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">1</span>
                <div>
                  Go to <strong>console.cloud.google.com</strong> → create or select a project.
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">2</span>
                <div>
                  Go to <strong>APIs &amp; Services → Library</strong> → search for <strong>"Google Search Console API"</strong> → Enable it.
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">3</span>
                <div>
                  Go to <strong>IAM &amp; Admin → Service Accounts</strong> → click <strong>Create Service Account</strong> → give it any name (e.g. <code class="font-mono bg-muted px-1 rounded">seo-engine</code>) → Done.
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">4</span>
                <div>
                  Click the service account you just created → <strong>Keys</strong> tab → <strong>Add Key → Create new key → JSON</strong> → download the file.
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">5</span>
                <div>
                  Move the downloaded JSON file into the <strong>SEO Engine project folder</strong> (same folder as <code class="font-mono bg-muted px-1 rounded">start.bat</code>).
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">6</span>
                <div>
                  <strong class="text-destructive">Important:</strong> Open the JSON file and copy the <code class="font-mono bg-muted px-1 rounded">client_email</code> value (looks like <code class="font-mono bg-muted px-1 rounded text-xs">seo-engine@my-project.iam.gserviceaccount.com</code>).
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">7</span>
                <div>
                  Go to <strong>search.google.com/search-console</strong> → select your property → <strong>Settings → Users and permissions → Add User</strong> → paste the email → set permission to <strong>Full</strong>.
                </div>
              </li>
            </ol>
            <Alert variant="success">
              That's it — no browser popup ever. The engine connects automatically using the JSON key.
            </Alert>
          </div>

          <!-- OAuth2 steps -->
          <div v-else class="space-y-3 text-sm">
            <ol class="space-y-3 list-none">
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">1</span>
                <div>
                  Go to <strong>console.cloud.google.com</strong> → create or select a project.
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">2</span>
                <div>
                  Go to <strong>APIs &amp; Services → Library</strong> → search for <strong>"Google Search Console API"</strong> → Enable it.
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">3</span>
                <div>
                  Go to <strong>OAuth consent screen</strong> → choose <strong>Internal</strong> (or External if needed) → fill in app name → Save.
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">4</span>
                <div>
                  Go to <strong>Credentials → Create Credentials → OAuth 2.0 Client ID</strong> → choose <strong>Desktop app</strong> → download the JSON.
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">5</span>
                <div>
                  Move the JSON file into the <strong>SEO Engine project folder</strong> and enter its filename below.
                </div>
              </li>
              <li class="flex gap-3">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">6</span>
                <div>
                  On the <strong>first pipeline run</strong>, a browser window will open asking you to sign in with Google and grant access. After that it saves a token and never asks again.
                </div>
              </li>
            </ol>
            <Alert variant="info">
              The token is saved to <code class="font-mono">gsc_token.json</code> in the project folder. Keep it out of git (already in .gitignore).
            </Alert>
          </div>

        </div>
      </div>

      <!-- Credentials file -->
      <div class="space-y-1.5">
        <Label>{{ $t('wizard.gsc.credentialsFile') }} <span class="text-destructive">*</span></Label>
        <Input
          v-model="wizard.form.gsc_credentials_file"
          placeholder="service-account-key.json"
          class="font-mono text-xs"
        />
        <p class="text-xs text-muted-foreground">
          Filename of the JSON key placed in the project root.
          The engine auto-detects whether it's a Service Account or OAuth2 file.
        </p>
      </div>

      <!-- GSC Site URL -->
      <div class="space-y-1.5">
        <Label>{{ $t('wizard.gsc.gscSiteUrl') }}</Label>
        <Input
          v-model="wizard.form.gsc_site_url"
          :placeholder="`https://${wizard.form.domain || 'yoursite.com'}/`"
          class="font-mono"
        />
        <p class="text-xs text-muted-foreground">{{ $t('wizard.gsc.gscSiteUrlHint') }}</p>
      </div>

      <!-- Protection thresholds -->
      <div class="border-t border-border pt-4">
        <p class="text-sm font-semibold text-foreground mb-3">{{ $t('wizard.gsc.thresholdsTitle') }}</p>
        <p class="text-xs text-muted-foreground mb-4">{{ $t('wizard.gsc.thresholdsHint') }}</p>
        <div class="grid grid-cols-3 gap-4">
          <div class="space-y-1.5">
            <Label>{{ $t('wizard.gsc.minClicks') }}</Label>
            <Input v-model.number="wizard.form.gsc_min_clicks" type="number" min="0" placeholder="10" />
          </div>
          <div class="space-y-1.5">
            <Label>{{ $t('wizard.gsc.minImpressions') }}</Label>
            <Input v-model.number="wizard.form.gsc_min_impressions" type="number" min="0" placeholder="100" />
          </div>
          <div class="space-y-1.5">
            <Label>{{ $t('wizard.gsc.maxPosition') }}</Label>
            <Input v-model.number="wizard.form.gsc_max_position" type="number" min="1" max="100" step="0.5" placeholder="20" />
          </div>
        </div>
      </div>

    </div>

    <div v-else class="text-center py-10">
      <p class="text-muted-foreground text-sm">{{ $t('wizard.gsc.laterNote') }}</p>
    </div>
  </div>
</template>
