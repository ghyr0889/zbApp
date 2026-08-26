
import { ref } from 'vue'
import { getLevelDefsApi } from '../api'

const DEFAULT = { job_grade: ['P1','P2','P3','P4'], difficulty: ['P1','P2','P3','P4'],
                  importance: ['Ⅰ级','Ⅱ级','Ⅲ级','Ⅳ级'], innovation: ['无','低','中','高'] }

let cached = null
const options = ref({ ...DEFAULT })

export function useLevelDefs() {
  if (!cached) {
    getLevelDefsApi()
      .then(res => {
        const d = res.data?.data
        if (d) {
          cached = d
          options.value = {
            difficulty: d.difficulty?.length ? d.difficulty : DEFAULT.difficulty,
            importance: d.importance?.length ? d.importance : DEFAULT.importance,
            innovation: d.innovation?.length ? d.innovation : DEFAULT.innovation
          }
        }
      })
      .catch(() => { /* 失败保持默认档位 */ })
  }
  return options
}