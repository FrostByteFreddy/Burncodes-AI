<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center">
    <div class="bg-gray-800 p-8 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
      <h2 class="text-2xl font-bold mb-6">Create New Tenant</h2>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label for="name" class="block text-sm font-medium text-gray-300">Tenant Name</label>
          <input v-model="formData.name" type="text" id="name" required
            class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg" />
        </div>
        <div>
          <label for="intro_message" class="block text-sm font-medium text-gray-300">Intro Message</label>
          <textarea v-model="formData.intro_message" id="intro_message" rows="3"
            class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg"></textarea>
        </div>
        <div>
          <label for="system_persona" class="block text-sm font-medium text-gray-300">System Persona</label>
          <textarea v-model="formData.system_persona" id="system_persona" rows="5"
            class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg"></textarea>
        </div>
        <div>
          <label for="rag_prompt_template" class="block text-sm font-medium text-gray-300">RAG Prompt Template</label>
          <textarea v-model="formData.rag_prompt_template" id="rag_prompt_template" rows="8"
            class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg"></textarea>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="doc_language" class="block text-sm font-medium text-gray-300">Document Language</label>
              <input v-model="formData.doc_language" type="text" id="doc_language" placeholder="e.g., en"
                class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg" />
            </div>
            <div>
              <label for="translation_target" class="block text-sm font-medium text-gray-300">Translation Target</label>
              <input v-model="formData.translation_target" type="text" id="translation_target" placeholder="e.g., English"
                class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg" />
            </div>
        </div>
        <div class="d-none">
            <label for="doc_description" class="block text-sm font-medium text-gray-300">Document Description</label>
            <input v-model="formData.doc_description" type="text" id="doc_description"
            class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg" />
        </div>
         <div class="d-none">
            <label for="source_description" class="block text-sm font-medium text-gray-300">Source Description</label>
            <input v-model="formData.source_description" type="text" id="source_description"
            class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg" />
        </div>
        <div class="d-none">
            <label for="last_updated_description" class="block text-sm font-medium text-gray-300">Last Updated Description</label>
            <input v-model="formData.last_updated_description" type="text" id="last_updated_description"
            class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg" />
        </div>
        <div class="flex justify-end space-x-4 pt-4">
          <button type="button" @click="$emit('close')"
            class="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg">Cancel</button>
          <button type="submit"
            class="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 rounded-lg">Create</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  show: Boolean
})

const emit = defineEmits(['close', 'create'])

const formData = ref({
  name: '',
  intro_message: 'Hello! I am a new chatbot. How can I help you today?',
  system_persona: 'You are a helpful and friendly AI assistant. Answer questions based on the provided context.',
  rag_prompt_template: '{persona}\n\nAnswer the following question based on the provided context.\n\n<context>\n{context}\n</context>\n\nQuestion: {input}\n',
  doc_language: 'en',
  doc_description: '',
  source_description: '',
  last_updated_description: '',
  translation_target: 'English'
})

const handleSubmit = () => {
  emit('create', { ...formData.value })
}
</script>
