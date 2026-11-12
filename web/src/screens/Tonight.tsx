import { useEffect, useState, type FormEvent } from 'react'
import { ApiError, GENERIC_ERROR, apiGet, apiPost } from '../api'
import { formatShortDate, formatToday, todayIso } from '../dates'
import { supabase } from '../supabase'
import { cleanTags, mergeTags } from '../tags'
import { NightSky } from './NightSky'
import type { NightsResponse } from '../nights'
import { Scores } from './Scores'

export const TAGS_OFF = 'Tag suggestions are off (no Claude API key).'
export const PRIVACY_LINE =
  "Suggest tags sends only your answers, the questions, and your tag list to Anthropic's " +
  'Claude API, never Oura data, your name, or email. Anthropic deletes API data within 30 days.'

type Load<T> = { state: 'loading' } | { state: 'ok'; data: T } | { state: 'error'; message: string }
type Pair = { question: string; answer: string }

function message(err: unknown): string {
  return err instanceof ApiError ? err.message : GENERIC_ERROR
}

/** Load once on mount. Errors become the API's plain message. */
function useLoad<T>(path: string): Load<T> {
  const [load, setLoad] = useState<Load<T>>({ state: 'loading' })
  useEffect(() => {
    let active = true
    apiGet<T>(path)
      .then((data) => active && setLoad({ state: 'ok', data }))
      .catch((err: unknown) => active && setLoad({ state: 'error', message: message(err) }))
    return () => {
      active = false
    }
  }, [path])
  return load
}

export function Tonight() {
  const nights = useLoad<NightsResponse>('/api/nights')
  const questionsLoad = useLoad<{ questions: string[] }>('/api/questions')
  const tagsStatus = useLoad<{ on: boolean }>('/api/tags/status')
  const questions = questionsLoad.state === 'ok' ? questionsLoad.data.questions : []
  const tagsOn = tagsStatus.state === 'ok' && tagsStatus.data.on

  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<string[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [suggested, setSuggested] = useState<string[]>([])
  const [newTags, setNewTags] = useState<string[]>([])
  const [suggesting, setSuggesting] = useState(false)
  const [suggestError, setSuggestError] = useState('')
  const [entryDate, setEntryDate] = useState(todayIso())
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [saved, setSaved] = useState('')

  const onTags = questions.length > 0 && step >= questions.length
  const answerAt = (i: number) => answers[i] ?? ''
  const pairs = (): Pair[] => questions.map((question, i) => ({ question, answer: answerAt(i) }))

  function setAnswer(i: number, text: string) {
    setSaved('')
    setAnswers((prev) => {
      const next = [...prev]
      next[i] = text
      return next
    })
  }

  function next(event: FormEvent) {
    event.preventDefault()
    setStep((s) => Math.min(s + 1, questions.length))
  }

  function addTag(event: FormEvent) {
    event.preventDefault()
    setTags((prev) => mergeTags(prev, cleanTags(newTag)))
    setNewTag('')
  }

  async function suggest() {
    setSuggesting(true)
    setSuggestError('')
    setNewTags([])
    try {
      const result = await apiPost<{ tags: { tag: string; is_new: boolean }[] }>('/api/tags/suggest', {
        pairs: pairs(),
      })
      const found = result.tags.map((t) => t.tag)
      setTags((prev) => mergeTags(prev, found))
      setSuggested(found)
      setNewTags(result.tags.filter((t) => t.is_new).map((t) => t.tag))
    } catch (err) {
      setSuggestError(message(err)) // existing tags are kept
    } finally {
      setSuggesting(false)
    }
  }

  async function save() {
    setSaving(true)
    setSaveError('')
    try {
      await apiPost('/api/entries', {
        entry_date: entryDate,
        answers: pairs(),
        tags,
        suggested_tags: suggested,
      })
      setSaved(`Saved your entry for ${formatShortDate(entryDate)}.`)
      setAnswers([])
      setTags([])
      setSuggested([])
      setNewTags([])
      setSuggestError('')
      setStep(0)
      setEntryDate(todayIso())
    } catch (err) {
      setSaveError(message(err)) // nothing is cleared
    } finally {
      setSaving(false)
    }
  }

  const answered = questions.slice(0, onTags ? questions.length : step)

  return (
    <>
      <NightSky date={formatToday()} title="Tonight" />
      <main className="content">
        {nights.state === 'ok' && <Scores data={nights.data} />}
        {nights.state === 'error' && (
          <p className="error" role="alert">
            {nights.message}
          </p>
        )}

        {saved && (
          <p className="note fade-in" role="status">
            {saved}
          </p>
        )}

        {questionsLoad.state === 'error' && (
          <p className="error" role="alert">
            {questionsLoad.message}
          </p>
        )}

        {answered.map((question, i) => (
          <div className="pair" key={question}>
            <p className="q">{question}</p>
            {answerAt(i).trim() ? <p className="a">{answerAt(i)}</p> : <p className="skipped">Skipped.</p>}
          </div>
        ))}

        {questions.length > 0 && !onTags && (
          <form className="fade-in" key={step} onSubmit={next}>
            <label className="q" htmlFor="answer">
              {questions[step]}
            </label>
            <textarea
              id="answer"
              className="field area"
              value={answerAt(step)}
              onChange={(e) => setAnswer(step, e.target.value)}
              rows={3}
            />
            <div className="row">
              {step > 0 && (
                <button className="button quiet" type="button" onClick={() => setStep(step - 1)}>
                  Back
                </button>
              )}
              <button className="button" type="submit">
                Next
              </button>
            </div>
          </form>
        )}

        {onTags && (
          <section className="fade-in tags-step" aria-label="Tags">
            <p className="tags-label">Tags</p>
            {tags.length > 0 ? (
              <ul className="tags">
                {tags.map((tag) => (
                  <li key={tag}>
                    <button
                      className="tag"
                      type="button"
                      aria-label={`Remove ${tag}`}
                      onClick={() => setTags((prev) => prev.filter((t) => t !== tag))}
                    >
                      {tag} <span aria-hidden="true">×</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="skipped">No tags yet.</p>
            )}

            <form className="row" onSubmit={addTag}>
              <label className="visually-hidden" htmlFor="new-tag">
                Add a tag
              </label>
              <input
                id="new-tag"
                className="field"
                placeholder="Add a tag"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
              />
              <button className="button quiet" type="submit" disabled={!newTag.trim()}>
                Add
              </button>
            </form>

            {tagsOn ? (
              <>
                <button className="button quiet" type="button" onClick={suggest} disabled={suggesting}>
                  Suggest tags
                </button>
                {newTags.length > 0 && (
                  <p className="small">New tags: {newTags.join(', ')}. Swap in an existing tag if one fits.</p>
                )}
                {suggestError && (
                  <p className="error" role="alert">
                    {suggestError}
                  </p>
                )}
                <p className="small">{PRIVACY_LINE}</p>
              </>
            ) : (
              tagsStatus.state !== 'loading' && <p className="small">{TAGS_OFF}</p>
            )}

            <label htmlFor="entry-date">Entry date</label>
            <input
              id="entry-date"
              className="field"
              type="date"
              value={entryDate}
              max={todayIso()}
              onChange={(e) => setEntryDate(e.target.value)}
            />

            {saveError && (
              <p className="error" role="alert">
                {saveError}
              </p>
            )}
            <div className="row">
              <button className="button quiet" type="button" onClick={() => setStep(questions.length - 1)}>
                Back
              </button>
              <button className="button" type="button" onClick={save} disabled={saving || !entryDate}>
                Save
              </button>
            </div>
          </section>
        )}

        <button className="button quiet sign-out" type="button" onClick={() => supabase.auth.signOut()}>
          Sign out
        </button>
      </main>
    </>
  )
}
