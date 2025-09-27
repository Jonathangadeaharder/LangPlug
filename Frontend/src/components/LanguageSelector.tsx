import React from 'react';
import styled from 'styled-components';

export interface Language {
  code: string;
  name: string;
  flag: string;
}

interface LanguageSelectorProps {
  label: string;
  selectedLanguage: Language;
  languages: Language[];
  onSelect: (language: Language) => void;
  disabled?: boolean;
}

const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  label,
  selectedLanguage,
  languages,
  onSelect,
  disabled = false
}) => {
  const helperLabel = disabled ? 'Changes disabled' : 'Tap to choose your language';

  const renderFlag = (flag: string, name: string) => {
    if (flag && /^[a-z]{2}$/i.test(flag)) {
      const code = flag.toLowerCase();
      return (
        <FlagImage
          src={`https://flagcdn.com/w40/${code}.png`}
          alt={`${name} flag`}
          loading="lazy"
        />
      );
    }

    if (flag && flag.trim().length > 0) {
      return <span>{flag}</span>;
    }

    return <FallbackFlag aria-hidden="true">{name.slice(0, 2).toUpperCase()}</FallbackFlag>;
  };

  return (
    <Container>
      <LabelRow>
        <Label>{label}</Label>
        <HelperText>{helperLabel}</HelperText>
      </LabelRow>
      <LanguageOptions>
        {languages.map((lang) => {
          const isSelected = selectedLanguage.code === lang.code;

          return (
            <LanguageOption
              key={lang.code}
              $selected={isSelected}
              $disabled={disabled}
              onClick={() => !disabled && onSelect(lang)}
              disabled={disabled}
              aria-pressed={isSelected}
            >
              {isSelected && <SelectionIndicator aria-hidden="true" />}
              <FlagBadge $selected={isSelected} aria-hidden="true">
                {renderFlag(lang.flag, lang.name)}
              </FlagBadge>
              <LanguageLabel>
                <LanguageCode $selected={isSelected}>{lang.code.toUpperCase()}</LanguageCode>
                <LanguageName $selected={isSelected}>{lang.name}</LanguageName>
              </LanguageLabel>
            </LanguageOption>
          );
        })}
      </LanguageOptions>
    </Container>
  );
};

const Container = styled.div`
  margin: 20px 0;
`;

const LabelRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
`;

const Label = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
`;

const HelperText = styled.span`
  font-size: 13px;
  color: #6b7280;
`;

const LanguageOptions = styled.div`
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
`;

const LanguageOption = styled.button<{ $selected: boolean; $disabled: boolean }>`
  position: relative;
  padding: 18px 16px;
  border-radius: 16px;
  border: 1px solid ${props => props.$selected ? 'rgba(59, 130, 246, 0.6)' : 'rgba(148, 163, 184, 0.24)'};
  background: ${props => props.$selected
    ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(59, 130, 246, 0.04))'
    : 'rgba(255, 255, 255, 0.65)'};
  box-shadow: ${props => props.$selected
    ? '0 18px 40px rgba(59, 130, 246, 0.15)'
    : '0 12px 32px rgba(15, 23, 42, 0.08)'};
  backdrop-filter: blur(18px);
  cursor: ${props => props.$disabled ? 'not-allowed' : 'pointer'};
  opacity: ${props => props.$disabled ? 0.5 : 1};
  transition: transform 0.2s ease, box-shadow 0.2s ease, border 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;

  &:hover:not(:disabled) {
    transform: translateY(-3px);
    box-shadow: 0 22px 45px rgba(15, 23, 42, 0.12);
  }

  &:focus-visible {
    outline: 3px solid rgba(59, 130, 246, 0.35);
    outline-offset: 2px;
  }
`;

const FlagBadge = styled.div<{ $selected: boolean }>`
  height: 34px;
  display: flex;
  align-items: center;
  filter: ${props => props.$selected ? 'none' : 'grayscale(15%)'};
`;

const FlagImage = styled.img`
  width: 40px;
  height: 28px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.4);
`;

const FallbackFlag = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(148, 163, 184, 0.12);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.1em;
`;

const LanguageLabel = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2px;
`;

const LanguageCode = styled.span<{ $selected: boolean }>`
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: ${props => props.$selected ? '#1d4ed8' : '#6b7280'};
`;

const LanguageName = styled.span<{ $selected: boolean }>`
  font-size: 16px;
  font-weight: 600;
  color: ${props => props.$selected ? '#111827' : '#334155'};
`;

const SelectionIndicator = styled.span`
  position: absolute;
  top: 14px;
  right: 14px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #1d4ed8;
  box-shadow: 0 0 0 4px rgba(29, 78, 216, 0.2);
  border: 2px solid white;
`;

export default LanguageSelector;
