import { Pressable, StyleSheet, Text } from 'react-native';
import { useColorScheme } from '@/hooks/useColorScheme';
import { useThemeStore } from '@/store/theme';
import { Colors } from '@/constants/colors';

const ICON: Record<'system' | 'light' | 'dark', string> = {
  system: '⚙',
  light: '☀',
  dark: '☾',
};

const LABEL: Record<'system' | 'light' | 'dark', string> = {
  system: 'Auto',
  light: 'Claro',
  dark: 'Escuro',
};

export function ThemeToggle() {
  const scheme = useColorScheme();
  const c = Colors[scheme];
  const preference = useThemeStore((s) => s.preference);
  const cycle = useThemeStore((s) => s.cycle);

  return (
    <Pressable
      onPress={cycle}
      hitSlop={10}
      accessibilityLabel={`Tema: ${LABEL[preference]}. Tocar pra alternar.`}
      style={({ pressed }) => [
        styles.button,
        { borderColor: c.border, opacity: pressed ? 0.6 : 1 },
      ]}
    >
      <Text style={[styles.icon, { color: c.text }]}>{ICON[preference]}</Text>
      <Text style={[styles.label, { color: c.textSecondary }]}>{LABEL[preference]}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: StyleSheet.hairlineWidth,
  },
  icon: { fontSize: 16, lineHeight: 18 },
  label: { fontSize: 12, fontWeight: '600' },
});
