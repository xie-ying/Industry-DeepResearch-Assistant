import { proxy } from 'valtio'
import * as knowledgeApi from '@/api/knowledge'
import type { KnowledgeBase, KnowledgeBaseWithDocuments, KBDocument } from '@/api/knowledge'

interface KnowledgeState {
  knowledgeBases: KnowledgeBase[]
  currentKnowledgeBase: KnowledgeBaseWithDocuments | null
  loading: boolean
  uploading: boolean
}

export const knowledgeState = proxy<KnowledgeState>({
  knowledgeBases: [],
  currentKnowledgeBase: null,
  loading: false,
  uploading: false,
})

export const knowledgeActions = {
  async fetchKnowledgeBases() {
    knowledgeState.loading = true
    try {
      const res = await knowledgeApi.getKnowledgeBases()
      knowledgeState.knowledgeBases = res.data
    } finally {
      knowledgeState.loading = false
    }
  },

  async createKnowledgeBase(name: string, description?: string) {
    const res = await knowledgeApi.createKnowledgeBase({ name, description })
    knowledgeState.knowledgeBases.unshift(res.data)
    return res.data
  },

  async fetchKnowledgeBase(kbId: string) {
    knowledgeState.loading = true
    try {
      const res = await knowledgeApi.getKnowledgeBase(kbId)
      knowledgeState.currentKnowledgeBase = res.data
      return res.data
    } finally {
      knowledgeState.loading = false
    }
  },

  async updateKnowledgeBase(kbId: string, name?: string, description?: string) {
    const res = await knowledgeApi.updateKnowledgeBase(kbId, { name, description })
    const index = knowledgeState.knowledgeBases.findIndex((kb) => kb.id === kbId)
    if (index !== -1) {
      knowledgeState.knowledgeBases[index] = res.data
    }
    if (knowledgeState.currentKnowledgeBase?.id === kbId) {
      knowledgeState.currentKnowledgeBase = {
        ...knowledgeState.currentKnowledgeBase,
        ...res.data,
      }
    }
    return res.data
  },

  async deleteKnowledgeBase(kbId: string) {
    await knowledgeApi.deleteKnowledgeBase(kbId)
    knowledgeState.knowledgeBases = knowledgeState.knowledgeBases.filter(
      (kb) => kb.id !== kbId
    )
    if (knowledgeState.currentKnowledgeBase?.id === kbId) {
      knowledgeState.currentKnowledgeBase = null
    }
  },

  async uploadDocument(kbId: string, file: File) {
    knowledgeState.uploading = true
    try {
      const res = await knowledgeApi.uploadDocument(kbId, file)
      // Refresh the knowledge base to get updated document list
      await knowledgeActions.fetchKnowledgeBase(kbId)
      // Also update the list to reflect the new document count
      await knowledgeActions.fetchKnowledgeBases()
      return res.data
    } finally {
      knowledgeState.uploading = false
    }
  },

  async refreshDocuments(kbId: string) {
    const res = await knowledgeApi.getDocuments(kbId)
    if (knowledgeState.currentKnowledgeBase?.id === kbId) {
      knowledgeState.currentKnowledgeBase.documents = res.data
    }
    return res.data
  },

  async deleteDocument(kbId: string, docId: string) {
    await knowledgeApi.deleteDocument(kbId, docId)
    if (knowledgeState.currentKnowledgeBase?.id === kbId) {
      knowledgeState.currentKnowledgeBase.documents =
        knowledgeState.currentKnowledgeBase.documents.filter((doc) => doc.id !== docId)
      knowledgeState.currentKnowledgeBase.document_count = Math.max(
        0,
        knowledgeState.currentKnowledgeBase.document_count - 1
      )
    }
    // Update the list
    const index = knowledgeState.knowledgeBases.findIndex((kb) => kb.id === kbId)
    if (index !== -1) {
      knowledgeState.knowledgeBases[index].document_count = Math.max(
        0,
        knowledgeState.knowledgeBases[index].document_count - 1
      )
    }
  },

  clearCurrentKnowledgeBase() {
    knowledgeState.currentKnowledgeBase = null
  },
}

export type { KnowledgeBase, KnowledgeBaseWithDocuments, KBDocument }
