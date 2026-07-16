import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import Disclaimer from './Disclaimer.vue'

describe('Disclaimer.vue', () => {
  it('renders the educational disclaimer text', () => {
    const wrapper = mount(Disclaimer)
    expect(wrapper.text()).toContain('Educational Purpose Only')
  })

  it('renders the warning', () => {
    const wrapper = mount(Disclaimer)
    expect(wrapper.text()).toContain('not investment advice')
  })
})
