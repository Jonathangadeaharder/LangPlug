import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import LanguageSelector, { Language } from '../components/LanguageSelector';
import { api, authService } from '../services/api';

const ProfileScreen: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [nativeLanguage, setNativeLanguage] = useState<Language>({ code: 'en', name: 'English', flag: '🇬🇧' });
  const [targetLanguage, setTargetLanguage] = useState<Language>({ code: 'de', name: 'German', flag: '🇩🇪' });
  const [hasChanges, setHasChanges] = useState(false);

  const supportedLanguages: Language[] = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'de', name: 'German', flag: '🇩🇪' },
    { code: 'es', name: 'Spanish', flag: '🇪🇸' },
  ];

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await api.get('/profile');
      const profileData = response.data;
      
      setProfile(profileData);
      setNativeLanguage({
        code: profileData.native_language.code,
        name: profileData.native_language.name,
        flag: profileData.native_language.flag,
      });
      setTargetLanguage({
        code: profileData.target_language.code,
        name: profileData.target_language.name,
        flag: profileData.target_language.flag,
      });
    } catch (error) {
      console.error('Error loading profile:', error);
      alert('Error: Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleNativeLanguageSelect = (language: Language) => {
    if (language.code === targetLanguage.code) {
      alert('Invalid Selection: Native language cannot be the same as target language');
      return;
    }
    setNativeLanguage(language);
    setHasChanges(true);
  };

  const handleTargetLanguageSelect = (language: Language) => {
    if (language.code === nativeLanguage.code) {
      alert('Invalid Selection: Target language cannot be the same as native language');
      return;
    }
    setTargetLanguage(language);
    setHasChanges(true);
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      const response = await api.put('/profile/languages', {
        native_language: nativeLanguage.code,
        target_language: targetLanguage.code,
      });
      
      if (response.data.success) {
        alert('Success: Language preferences saved successfully');
        setHasChanges(false);
        await loadProfile(); // Reload profile to get updated data
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      alert('Error: Failed to save language preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    if (confirm('Are you sure you want to logout?')) {
      try {
        await api.post('/auth/logout');
        localStorage.removeItem('authToken');
        // Navigation to login screen would happen here
        // For now just show a message
        alert('Success: Logged out successfully');
      } catch (error) {
        console.error('Logout error:', error);
        alert('Error: Failed to logout');
      }
    }
  };

  if (loading) {
    return (
      <LoadingContainer>
        <LoadingSpinner />
        <LoadingText>Loading profile...</LoadingText>
      </LoadingContainer>
    );
  }

  return (
    <Container>
      <Header>
        <Title>Profile</Title>
      </Header>

      {profile && (
        <UserInfo>
          <Username>{profile.username}</Username>
          {profile.is_superuser && (
            <AdminBadge>
              <AdminText>Admin</AdminText>
            </AdminBadge>
          )}
          <MemberSince>
            Member since: {new Date(profile.created_at).toLocaleDateString()}
          </MemberSince>
          {profile.last_login && (
            <LastLogin>
              Last login: {new Date(profile.last_login).toLocaleString()}
            </LastLogin>
          )}
        </UserInfo>
      )}

      <Section>
        <SectionTitle>Language Preferences</SectionTitle>
        
        <LanguageSelector
          label="Native Language"
          selectedLanguage={nativeLanguage}
          languages={supportedLanguages}
          onSelect={handleNativeLanguageSelect}
          disabled={saving}
        />

        <LanguageSelector
          label="Learning Language"
          selectedLanguage={targetLanguage}
          languages={supportedLanguages}
          onSelect={handleTargetLanguageSelect}
          disabled={saving}
        />

        {hasChanges && (
          <SaveButton
            $disabled={saving}
            onClick={savePreferences}
            disabled={saving}
          >
            {saving ? (
              <LoadingSpinner />
            ) : (
              <ButtonText>Save Changes</ButtonText>
            )}
          </SaveButton>
        )}
      </Section>

      <Section>
        <LogoutButton onClick={handleLogout}>
          <ButtonText>Logout</ButtonText>
        </LogoutButton>
      </Section>
    </Container>
  );
};

const Container = styled.div`
  min-height: 100vh;
  background-color: #fff;
  overflow-y: auto;
`;

const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #fff;
`;

const LoadingSpinner = styled.div`
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #2196F3;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const LoadingText = styled.div`
  margin-top: 10px;
  color: #666;
`;

const Header = styled.div`
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
`;

const Title = styled.h1`
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin: 0;
`;

const UserInfo = styled.div`
  padding: 20px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
`;

const Username = styled.div`
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
`;

const AdminBadge = styled.div`
  background-color: #ff9800;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 8px;
`;

const AdminText = styled.div`
  color: white;
  font-size: 12px;
  font-weight: bold;
`;

const MemberSince = styled.div`
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
`;

const LastLogin = styled.div`
  font-size: 14px;
  color: #666;
`;

const Section = styled.div`
  padding: 20px;
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  margin-top: 0;
`;

const SaveButton = styled.button<{ $disabled: boolean }>`
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 14px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
  cursor: ${props => props.$disabled ? 'not-allowed' : 'pointer'};
  opacity: ${props => props.$disabled ? 0.6 : 1};
  transition: background-color 0.2s ease;

  &:hover:not(:disabled) {
    background-color: #1976D2;
  }
`;

const LogoutButton = styled.button`
  background-color: #f44336;
  color: white;
  border: none;
  padding: 14px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: #d32f2f;
  }
`;

const ButtonText = styled.span`
  font-size: 16px;
  font-weight: 600;
`;

export default ProfileScreen;