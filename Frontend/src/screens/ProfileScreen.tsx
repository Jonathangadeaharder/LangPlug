import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { toast } from 'react-hot-toast'
import { ArrowLeftIcon } from '@heroicons/react/24/solid'
import LanguageSelector, { type Language } from '@/components/LanguageSelector'
import * as Services from '@/client/services.gen'
import { useAuthStore } from '@/store/useAuthStore'

const LANGUAGE_LIBRARY: Language[] = [
  { code: 'en', name: 'English', flag: 'us' },
  { code: 'de', name: 'German', flag: 'de' },
  { code: 'es', name: 'Spanish', flag: 'es' },
  { code: 'fr', name: 'French', flag: 'fr' },
  { code: 'zh', name: 'Chinese', flag: 'cn' },
]

// Supported translation pairs (native -> target)
const SUPPORTED_TRANSLATION_PAIRS: [string, string][] = [
  ['es', 'de'], // Spanish native learning German
  ['es', 'en'], // Spanish native learning English
  ['en', 'zh'], // English native learning Chinese
  ['de', 'es'], // German native learning Spanish
  ['de', 'fr'], // German native learning French
]

const isTranslationPairSupported = (native: string, target: string): boolean => {
  return SUPPORTED_TRANSLATION_PAIRS.some(([n, t]) => n === native && t === target)
}

interface ProfileLanguage {
  code: string
  name: string
  flag: string
}

interface ProfileResponse {
  username: string
  email: string
  created_at: string
  last_login?: string | null
  is_superuser?: boolean
  native_language: ProfileLanguage
  target_language: ProfileLanguage
}

const ProfileScreen: React.FC = () => {
  const navigate = useNavigate()
  const { logout } = useAuthStore()

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [profile, setProfile] = useState<ProfileResponse | null>(null)
  const [languageOptions, setLanguageOptions] = useState<Language[]>(LANGUAGE_LIBRARY)
  const [nativeLanguage, setNativeLanguage] = useState<Language>(LANGUAGE_LIBRARY[0])
  const [targetLanguage, setTargetLanguage] = useState<Language>(LANGUAGE_LIBRARY[1])
  const [hasChanges, setHasChanges] = useState(false)

  const initials = useMemo(() => {
    if (!profile?.username) return 'LP'
    const parts = profile.username.split(' ').filter(Boolean)
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  }, [profile?.username])

  useEffect(() => {
    loadProfile()
  }, [])

  const ensureLanguageInOptions = (lang: ProfileLanguage) => {
    setLanguageOptions(prev => {
      if (prev.some(item => item.code === lang.code)) {
        return prev
      }
      return [...prev, { code: lang.code, name: lang.name, flag: lang.flag }]
    })
  }

  const findLanguage = (lang: ProfileLanguage): Language => {
    const pool = [...languageOptions, ...LANGUAGE_LIBRARY]
    const match = pool.find(item => item.code === lang.code)
    return match ?? { code: lang.code, name: lang.name, flag: lang.flag }
  }

  const loadProfile = async () => {
    try {
      setLoading(true)
      const profileData = await Services.profileGetApiProfileGet() as ProfileResponse

      if (!profileData) {
        toast.error('Could not load profile details.')
        return
      }

      ensureLanguageInOptions(profileData.native_language)
      ensureLanguageInOptions(profileData.target_language)

      setProfile(profileData)
      setNativeLanguage(findLanguage(profileData.native_language))
      setTargetLanguage(findLanguage(profileData.target_language))
      setHasChanges(false)
    } catch (error) {
      toast.error('Something went wrong while loading your profile.')
      console.error('Profile load error', error)
    } finally {
      setLoading(false)
    }
  }

  const handleNativeLanguageSelect = (language: Language) => {
    if (language.code === targetLanguage.code) {
      toast.error('Native and learning language must be different.')
      return
    }

    // Check if this pair is supported
    if (!isTranslationPairSupported(language.code, targetLanguage.code)) {
      toast.error(`Translation from ${language.name} to ${targetLanguage.name} is not supported yet.`)
      return
    }

    setNativeLanguage(language)
    setHasChanges(true)
  }

  const handleTargetLanguageSelect = (language: Language) => {
    if (language.code === nativeLanguage.code) {
      toast.error('Native and learning language must be different.')
      return
    }

    // Check if this pair is supported
    if (!isTranslationPairSupported(nativeLanguage.code, language.code)) {
      toast.error(`Translation from ${nativeLanguage.name} to ${language.name} is not supported yet.`)
      return
    }

    setTargetLanguage(language)
    setHasChanges(true)
  }

  const savePreferences = async () => {
    try {
      setSaving(true)
      await Services.profileUpdateLanguagesApiProfileLanguagesPut({
        requestBody: {
          native_language: nativeLanguage.code,
          target_language: targetLanguage.code,
        },
      })
      toast.success('Your language preferences are saved.')
      setHasChanges(false)
      await loadProfile()
    } catch (error) {
      toast.error('Could not save your preferences.')
      console.error('Profile save error', error)
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
      toast.success('See you soon!')
      navigate('/login')
    } catch (error) {
      toast.error('Failed to log you out. Please try again.')
      console.error('Logout error', error)
    }
  }

  const handleBackHome = () => {
    navigate('/')
  }

  const canSave = hasChanges && !saving

  if (loading) {
    return (
      <PageWrapper>
        <CenteredState>
          <LoadingSpinner />
          <LoadingText>Preparing your profile...</LoadingText>
        </CenteredState>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper>
      <Content>
        <HeaderRow>
          <BackButton onClick={handleBackHome}>
            <ArrowLeftIcon aria-hidden="true" />
            Back to dashboard
          </BackButton>
          <LogoutGhostButton onClick={handleLogout}>Log out</LogoutGhostButton>
        </HeaderRow>

        <HeroCard>
          <Avatar>{initials}</Avatar>
          <HeroContent>
          <HeroTitle>Hello {profile?.username ?? 'Explorer'}</HeroTitle>
            <HeroSubtitle>
              Personalize your language journey by choosing the languages you speak and the ones you want to master.
            </HeroSubtitle>
            <HeroStats>
              <Stat>
                <StatLabel>Member since</StatLabel>
                <StatValue>{profile ? new Date(profile.created_at).toLocaleDateString() : '—'}</StatValue>
              </Stat>
              {profile?.last_login && (
                <Stat>
                  <StatLabel>Last active</StatLabel>
                  <StatValue>{new Date(profile.last_login).toLocaleString()}</StatValue>
                </Stat>
              )}
              {profile?.is_superuser && (
                <Stat>
                  <StatLabel>Status</StatLabel>
                  <AdminBadge>Admin</AdminBadge>
                </Stat>
              )}
            </HeroStats>
          </HeroContent>
        </HeroCard>

        <PreferencesCard>
          <SectionHeading>Language preferences</SectionHeading>
          <SectionDescription>
            Tell us about your language goals so we can tailor vocabulary, subtitles, and exercises just for you.
          </SectionDescription>

          <SelectorGrid>
            <GlassPanel>
              <PanelLabel>Your native language</PanelLabel>
              <LanguageSelector
                label="Native language"
                selectedLanguage={nativeLanguage}
                languages={languageOptions}
                onSelect={handleNativeLanguageSelect}
                disabled={saving}
              />
            </GlassPanel>

            <GlassPanel>
              <PanelLabel>Language you want to learn</PanelLabel>
              <LanguageSelector
                label="Learning language"
                selectedLanguage={targetLanguage}
                languages={languageOptions}
                onSelect={handleTargetLanguageSelect}
                disabled={saving}
              />
            </GlassPanel>
          </SelectorGrid>

          <ActionRow>
            <StatusPill $success={!hasChanges}>
              {hasChanges ? 'Unsaved changes' : 'All changes saved'}
            </StatusPill>
            <PrimaryButton onClick={savePreferences} disabled={!canSave}>
              {saving ? 'Saving...' : 'Save preferences'}
            </PrimaryButton>
          </ActionRow>
        </PreferencesCard>
      </Content>
    </PageWrapper>
  )
}

const PageWrapper = styled.div`
  min-height: 100vh;
  background: radial-gradient(circle at 10% 20%, #111827 0%, #020617 55%);
  padding: 0 24px 120px;
  color: white;
`

const Content = styled.div`
  max-width: 1080px;
  margin: 0 auto;
  padding-top: 92px;
`

const HeaderRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
`

const GlassButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(15, 23, 42, 0.55);
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 32px rgba(15, 23, 42, 0.35);
    border-color: rgba(59, 130, 246, 0.35);
  }

  &:focus-visible {
    outline: 3px solid rgba(59, 130, 246, 0.5);
    outline-offset: 2px;
  }

  svg {
    width: 18px;
    height: 18px;
  }
`

const BackButton = styled(GlassButton)`
  font-size: 15px;
`

const LogoutGhostButton = styled(GlassButton)`
  background: rgba(248, 113, 113, 0.18);
  border-color: rgba(248, 113, 113, 0.35);
  color: #fecaca;

  &:hover {
    border-color: rgba(248, 113, 113, 0.55);
    box-shadow: 0 16px 32px rgba(248, 113, 113, 0.28);
  }
`

const HeroCard = styled.section`
  display: grid;
  gap: 24px;
  grid-template-columns: auto 1fr;
  align-items: center;
  padding: 36px 40px;
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.3), rgba(15, 118, 110, 0.2));
  box-shadow: 0 28px 60px rgba(30, 64, 175, 0.25);
  margin-bottom: 40px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    text-align: center;
    padding: 28px;
  }
`

const Avatar = styled.div`
  width: 96px;
  height: 96px;
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(148, 163, 184, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
`

const HeroContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 18px;
`

const HeroTitle = styled.h1`
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;

  @media (max-width: 768px) {
    font-size: 28px;
  }
`

const HeroSubtitle = styled.p`
  color: rgba(226, 232, 240, 0.78);
  font-size: 17px;
  line-height: 1.6;
  max-width: 560px;
`

const HeroStats = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
`

const Stat = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
`

const StatLabel = styled.span`
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(226, 232, 240, 0.55);
`

const StatValue = styled.span`
  font-size: 18px;
  font-weight: 600;
  color: rgba(226, 232, 240, 0.92);
`

const AdminBadge = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(247, 181, 0, 0.2);
  color: #fde68a;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
`

const PreferencesCard = styled.section`
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(24px);
  padding: 40px;
  box-shadow: 0 32px 60px rgba(15, 23, 42, 0.35);

  @media (max-width: 768px) {
    padding: 28px 24px;
  }
`

const SectionHeading = styled.h2`
  font-size: 28px;
  font-weight: 700;
`

const SectionDescription = styled.p`
  margin-top: 12px;
  max-width: 620px;
  color: rgba(226, 232, 240, 0.7);
  line-height: 1.6;
`

const SelectorGrid = styled.div`
  display: grid;
  gap: 24px;
  margin-top: 32px;

  @media (min-width: 900px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
`

const GlassPanel = styled.div`
  border-radius: 20px;
  padding: 20px 24px;
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
`

const PanelLabel = styled.h3`
  font-size: 15px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(226, 232, 240, 0.7);
  margin-bottom: 12px;
`

const ActionRow = styled.div`
  margin-top: 36px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
`

const StatusPill = styled.span<{ $success: boolean }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.04em;
  color: ${props => props.$success ? '#34d399' : '#facc15'};
  background: ${props => props.$success ? 'rgba(16, 185, 129, 0.18)' : 'rgba(234, 179, 8, 0.18)'};
  border: 1px solid ${props => props.$success ? 'rgba(16, 185, 129, 0.35)' : 'rgba(234, 179, 8, 0.35)'};
`

const PrimaryButton = styled.button`
  padding: 14px 28px;
  border-radius: 999px;
  border: none;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: white;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  box-shadow: 0 18px 40px rgba(37, 99, 235, 0.35);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 22px 50px rgba(37, 99, 235, 0.4);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    box-shadow: none;
  }
`

const CenteredState = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: rgba(226, 232, 240, 0.75);
`

const LoadingSpinner = styled.div`
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 4px solid rgba(148, 163, 184, 0.25);
  border-top-color: #60a5fa;
  animation: spin 1s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`

const LoadingText = styled.span`
  font-size: 16px;
`

export default ProfileScreen
