<template>
  <header class="page-intro">
    <h1>{{ title }}</h1>
    <p v-if="description">{{ description }}</p>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' }
})
</script>
