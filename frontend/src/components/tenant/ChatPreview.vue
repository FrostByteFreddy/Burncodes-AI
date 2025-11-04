<template>
    <iframe :src="`/chat/${tenantId}`" class="w-full h-[600px] py-5 bg-base-200"
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