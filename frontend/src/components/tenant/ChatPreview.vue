<template>
    <iframe :src="`/chat/${tenantId}`" class="w-full h-screen max-h-[80svh] py-5 bg-base-200"
        title="Chat Preview"></iframe>
</template>

<script setup>
defineProps({
    tenantId: {
        type: String,
        required: true
    }
});
</script>