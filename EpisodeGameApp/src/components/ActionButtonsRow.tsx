import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';

interface ActionButton {
  id: string;
  title: string;
  icon?: string;
  onPress: () => void;
  style?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'custom';
  backgroundColor?: string;
  textColor?: string;
  disabled?: boolean;
}

interface ActionButtonsRowProps {
  buttons: ActionButton[];
  layout?: 'horizontal' | 'vertical';
  spacing?: number;
  style?: ViewStyle;
  buttonStyle?: ViewStyle;
}

const ActionButtonsRow: React.FC<ActionButtonsRowProps> = ({
  buttons,
  layout = 'horizontal',
  spacing = 12,
  style,
  buttonStyle,
}) => {
  const getButtonStyle = (button: ActionButton) => {
    const baseStyle = [styles.button, buttonStyle];
    
    if (button.disabled) {
      baseStyle.push(styles.disabledButton);
    } else {
      switch (button.style) {
        case 'primary':
          baseStyle.push(styles.primaryButton);
          break;
        case 'secondary':
          baseStyle.push(styles.secondaryButton);
          break;
        case 'success':
          baseStyle.push(styles.successButton);
          break;
        case 'warning':
          baseStyle.push(styles.warningButton);
          break;
        case 'danger':
          baseStyle.push(styles.dangerButton);
          break;
        case 'custom':
          if (button.backgroundColor) {
            baseStyle.push({ backgroundColor: button.backgroundColor });
          }
          break;
        default:
          baseStyle.push(styles.primaryButton);
      }
    }
    
    return baseStyle;
  };

  const getTextStyle = (button: ActionButton) => {
    const baseStyle = [styles.buttonText];
    
    if (button.disabled) {
      baseStyle.push(styles.disabledButtonText);
    } else {
      switch (button.style) {
        case 'secondary':
          baseStyle.push(styles.secondaryButtonText);
          break;
        case 'custom':
          if (button.textColor) {
            baseStyle.push({ color: button.textColor });
          }
          break;
        default:
          baseStyle.push(styles.primaryButtonText);
      }
    }
    
    return baseStyle;
  };

  const containerStyle = [
    styles.container,
    layout === 'vertical' ? styles.verticalLayout : styles.horizontalLayout,
    { gap: spacing },
    style,
  ];

  return (
    <View style={containerStyle}>
      {buttons.map((button) => (
        <TouchableOpacity
          key={button.id}
          style={getButtonStyle(button)}
          onPress={button.onPress}
          disabled={button.disabled}
          activeOpacity={0.8}
        >
          <Text style={getTextStyle(button)}>
            {button.icon && `${button.icon} `}{button.title}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

// Helper function to create common button configurations
export const createCommonButtons = ({
  onWatchVideo,
  onPlayAgain,
  onViewResults,
  onBackToGame,
  onSubmit,
  onSkip,
}: {
  onWatchVideo?: () => void;
  onPlayAgain?: () => void;
  onViewResults?: () => void;
  onBackToGame?: () => void;
  onSubmit?: () => void;
  onSkip?: () => void;
}): ActionButton[] => {
  const buttons: ActionButton[] = [];
  
  if (onWatchVideo) {
    buttons.push({
      id: 'watch-video',
      title: 'Watch Episode',
      icon: '📺',
      onPress: onWatchVideo,
      style: 'warning',
    });
  }
  
  if (onPlayAgain) {
    buttons.push({
      id: 'play-again',
      title: 'Play Again',
      icon: '🔄',
      onPress: onPlayAgain,
      style: 'primary',
    });
  }
  
  if (onViewResults) {
    buttons.push({
      id: 'view-results',
      title: 'View Results',
      icon: '📊',
      onPress: onViewResults,
      style: 'secondary',
    });
  }
  
  if (onBackToGame) {
    buttons.push({
      id: 'back-to-game',
      title: 'Back to Game',
      icon: '←',
      onPress: onBackToGame,
      style: 'secondary',
    });
  }
  
  if (onSubmit) {
    buttons.push({
      id: 'submit',
      title: 'Submit Answer',
      onPress: onSubmit,
      style: 'success',
    });
  }
  
  if (onSkip) {
    buttons.push({
      id: 'skip',
      title: 'Skip',
      icon: '⏭',
      onPress: onSkip,
      style: 'warning',
    });
  }
  
  return buttons;
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: '#FFFFFF',
  },
  horizontalLayout: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    flexWrap: 'wrap',
  },
  verticalLayout: {
    flexDirection: 'column',
  },
  button: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 120,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  primaryButton: {
    backgroundColor: '#2196F3',
  },
  secondaryButton: {
    backgroundColor: '#FFFFFF',
    borderWidth: 2,
    borderColor: '#2196F3',
  },
  successButton: {
    backgroundColor: '#4CAF50',
  },
  warningButton: {
    backgroundColor: '#FF9800',
  },
  dangerButton: {
    backgroundColor: '#F44336',
  },
  disabledButton: {
    backgroundColor: '#CCCCCC',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  primaryButtonText: {
    color: '#FFFFFF',
  },
  secondaryButtonText: {
    color: '#2196F3',
  },
  disabledButtonText: {
    color: '#999999',
  },
});

export default ActionButtonsRow;