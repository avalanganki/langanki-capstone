import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { NIGHTS, QUESTIONS, fakeApi, sentBody } from '../test/fakeApi'
import { fakeSession, resetSupabase } from '../test/supabaseMock'

vi.mock('../supabase', () => import('../test/supabaseMock'))

const { Tonight, PRIVACY_LINE, TAGS_OFF } = await import('./Tonight')
const { todayIso } = await import('../dates')

const [Q1, Q2, Q3] = QUESTIONS
const ANSWER = 'Flat until a 3pm espresso' // synthetic

async function answer(text: string) {
  const box = await screen.findByRole('textbox', { name: /\?$/ })
  if (text) await userEvent.type(box, text)
  await userEvent.click(screen.getByRole('button', { name: 'Next' }))
}

async function toTags(first = ANSWER) {
  await answer(first)
  await answer('')
  await answer('Reading')
  await screen.findByRole('region', { name: 'Tags' })
}

function tagPills() {
  const list = screen.queryByRole('list')
  return list ? within(list).getAllByRole('button').map((b) => b.textContent?.replace(' ×', '')) : []
}

describe('Tonight', () => {
  beforeEach(() => resetSupabase(fakeSession))
  afterEach(() => vi.unstubAllGlobals())

  describe('scores', () => {
    it("shows last night's rings and HRV, with No data for a missing value", async () => {
      fakeApi()
      render(<Tonight />)
      expect(await screen.findByRole('group', { name: 'Sleep: 81' })).toBeInTheDocument()
      expect(screen.getByRole('group', { name: 'Readiness: No data' })).toBeInTheDocument()
      expect(screen.getByRole('group', { name: 'HRV (ms): 52.3' })).toBeInTheDocument()
      expect(screen.queryByText('0')).not.toBeInTheDocument()
      expect(screen.getByText('Last night, Jan 2. From your Oura ring.')).toBeInTheDocument()
    })

    it('labels sample nights as sample', async () => {
      fakeApi({ 'GET /api/nights': { status: 200, body: { ...NIGHTS, source: 'sample' } } })
      render(<Tonight />)
      expect(await screen.findByText('Last night, Jan 2. Sample data. Not real Oura data.')).toBeInTheDocument()
    })

    it("shows the nights error and still asks the questions", async () => {
      fakeApi({ 'GET /api/nights': { status: 503, body: { detail: "Couldn't reach the database. Try again." } } })
      render(<Tonight />)
      expect(await screen.findByText("Couldn't reach the database. Try again.")).toBeInTheDocument()
      expect(await screen.findByLabelText(Q1)).toBeInTheDocument()
    })
  })

  describe('questions', () => {
    it('asks one question at a time and keeps earlier answers above', async () => {
      fakeApi()
      render(<Tonight />)
      expect(await screen.findByLabelText(Q1)).toBeInTheDocument()
      expect(screen.queryByText(Q2)).not.toBeInTheDocument()

      await answer(ANSWER)
      expect(screen.getByLabelText(Q2)).toBeInTheDocument()
      expect(screen.getByText(Q1)).toBeInTheDocument()
      expect(screen.getByText(ANSWER)).toBeInTheDocument()
      expect(screen.queryByText(Q3)).not.toBeInTheDocument()
    })

    it('a blank Next skips the question', async () => {
      fakeApi()
      render(<Tonight />)
      await answer('')
      expect(screen.getByText('Skipped.')).toBeInTheDocument()
      expect(screen.getByLabelText(Q2)).toBeInTheDocument()
    })

    it('Back returns to the previous question with its answer kept', async () => {
      fakeApi()
      render(<Tonight />)
      await answer(ANSWER)
      await userEvent.click(screen.getByRole('button', { name: 'Back' }))
      expect(screen.getByLabelText(Q1)).toHaveValue(ANSWER)
      expect(screen.queryByRole('button', { name: 'Back' })).not.toBeInTheDocument()
    })

    it('after the last question, shows tags and Back returns to it', async () => {
      fakeApi()
      render(<Tonight />)
      await toTags()
      for (const q of QUESTIONS) expect(screen.getByText(q)).toBeInTheDocument()
      await userEvent.click(screen.getByRole('button', { name: 'Back' }))
      expect(screen.getByLabelText(Q3)).toHaveValue('Reading')
    })
  })

  describe('tags', () => {
    it('adds cleaned tags and removes a tag on tap', async () => {
      fakeApi()
      render(<Tonight />)
      await toTags()
      const field = screen.getByLabelText('Add a tag')
      await userEvent.type(field, ' Late Caffeine, stress,STRESS {enter}')
      expect(tagPills()).toEqual(['late caffeine', 'stress'])
      expect(field).toHaveValue('')

      await userEvent.click(screen.getByRole('button', { name: 'Remove late caffeine' }))
      expect(tagPills()).toEqual(['stress'])
    })

    it('hides Suggest tags when off and says so', async () => {
      fakeApi({ 'GET /api/tags/status': { status: 200, body: { on: false } } })
      render(<Tonight />)
      await toTags()
      expect(await screen.findByText(TAGS_OFF)).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: 'Suggest tags' })).not.toBeInTheDocument()
    })

    it('Suggest tags sends only the pairs, merges after typed tags, and names new tags', async () => {
      const fetchMock = fakeApi({
        'POST /api/tags/suggest': {
          status: 200,
          body: { tags: [{ tag: 'stress', is_new: false }, { tag: 'low energy', is_new: false }, { tag: 'espresso', is_new: true }] },
        },
      })
      render(<Tonight />)
      await toTags()
      await userEvent.type(screen.getByLabelText('Add a tag'), 'nap, stress{enter}')
      expect(screen.getByText(PRIVACY_LINE)).toBeInTheDocument()
      await userEvent.click(screen.getByRole('button', { name: 'Suggest tags' }))

      expect(await screen.findByText('New tags: espresso. Swap in an existing tag if one fits.')).toBeInTheDocument()
      expect(tagPills()).toEqual(['nap', 'stress', 'low energy', 'espresso'])
      expect(sentBody(fetchMock, 'POST', '/api/tags/suggest')).toEqual({
        pairs: [
          { question: Q1, answer: ANSWER },
          { question: Q2, answer: '' },
          { question: Q3, answer: 'Reading' },
        ],
      })
    })

    it('a suggest error shows the message and keeps the tags', async () => {
      fakeApi({
        'POST /api/tags/suggest': { status: 503, body: { detail: "Couldn't suggest tags right now. Type them instead." } },
      })
      render(<Tonight />)
      await toTags()
      await userEvent.type(screen.getByLabelText('Add a tag'), 'nap{enter}')
      await userEvent.click(screen.getByRole('button', { name: 'Suggest tags' }))
      expect(await screen.findByText("Couldn't suggest tags right now. Type them instead.")).toBeInTheDocument()
      expect(tagPills()).toEqual(['nap'])
    })
  })

  describe('save', () => {
    it('sends all answers, tags, and suggested tags, then clears the form', async () => {
      const fetchMock = fakeApi({
        'POST /api/tags/suggest': { status: 200, body: { tags: [{ tag: 'low energy', is_new: false }] } },
      })
      render(<Tonight />)
      await toTags()
      await userEvent.type(screen.getByLabelText('Add a tag'), 'nap{enter}')
      await userEvent.click(screen.getByRole('button', { name: 'Suggest tags' }))
      await screen.findByRole('button', { name: 'Remove low energy' })
      await userEvent.click(screen.getByRole('button', { name: 'Save' }))

      const today = todayIso()
      const [y, m, d] = today.split('-').map(Number)
      const short = new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      expect(await screen.findByText(`Saved your entry for ${short}.`)).toBeInTheDocument()
      expect(sentBody(fetchMock, 'POST', '/api/entries')).toEqual({
        entry_date: today,
        answers: [
          { question: Q1, answer: ANSWER },
          { question: Q2, answer: '' },
          { question: Q3, answer: 'Reading' },
        ],
        tags: ['nap', 'low energy'],
        suggested_tags: ['low energy'],
      })
      expect(screen.getByLabelText(Q1)).toHaveValue('')
      expect(screen.queryByText(ANSWER)).not.toBeInTheDocument()
    })

    it('uses the chosen entry date', async () => {
      const fetchMock = fakeApi()
      render(<Tonight />)
      await toTags()
      const date = screen.getByLabelText('Entry date')
      await userEvent.clear(date)
      await userEvent.type(date, '2000-01-05')
      await userEvent.click(screen.getByRole('button', { name: 'Save' }))
      expect(await screen.findByText('Saved your entry for Jan 5.')).toBeInTheDocument()
      expect((sentBody(fetchMock, 'POST', '/api/entries') as { entry_date: string }).entry_date).toBe('2000-01-05')
    })

    it('a duplicate date shows the message and keeps everything', async () => {
      const detail = 'You already have an entry for this date. Edit it in Past entries.'
      fakeApi({ 'POST /api/entries': { status: 409, body: { detail } } })
      render(<Tonight />)
      await toTags()
      await userEvent.type(screen.getByLabelText('Add a tag'), 'nap{enter}')
      await userEvent.click(screen.getByRole('button', { name: 'Save' }))
      expect(await screen.findByText(detail)).toBeInTheDocument()
      expect(screen.getByText(ANSWER)).toBeInTheDocument()
      expect(tagPills()).toEqual(['nap'])
    })

    it('all blank shows the API message', async () => {
      const detail = 'Answer at least one question to save.'
      fakeApi({ 'POST /api/entries': { status: 400, body: { detail } } })
      render(<Tonight />)
      await toTags('')
      await userEvent.click(screen.getByRole('button', { name: 'Save' }))
      expect(await screen.findByText(detail)).toBeInTheDocument()
    })

    it('never logs answers, tags, or scores', async () => {
      const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((m) =>
        vi.spyOn(console, m).mockImplementation(() => {}),
      )
      fakeApi({ 'POST /api/entries': { status: 409, body: { detail: 'dup' } } })
      render(<Tonight />)
      await toTags()
      await userEvent.type(screen.getByLabelText('Add a tag'), 'nap{enter}')
      await userEvent.click(screen.getByRole('button', { name: 'Save' }))
      await screen.findByText('dup')
      for (const spy of spies) {
        const logged = JSON.stringify(spy.mock.calls)
        expect(logged).not.toContain(ANSWER)
        expect(logged).not.toContain('nap')
        expect(logged).not.toContain('52.25')
        spy.mockRestore()
      }
    })
  })
})
