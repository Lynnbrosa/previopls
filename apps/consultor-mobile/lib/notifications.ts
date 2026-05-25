import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export async function requestPermissions(): Promise<boolean> {
  if (Platform.OS === 'web') return false;
  if (!Device.isDevice && Platform.OS !== 'android') return false;

  const { status: existing } = await Notifications.getPermissionsAsync();
  if (existing === 'granted') return true;

  const { status } = await Notifications.requestPermissionsAsync();
  return status === 'granted';
}

export async function notifyNewCriticalLead(
  leadId: string,
  nomeCliente: string,
  modeloVeiculo: string,
): Promise<void> {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: '🚨 Lead crítico',
      body: `${nomeCliente} — ${modeloVeiculo}. Aja antes da 1ª revisão.`,
      data: { leadId },
      sound: 'default',
    },
    trigger: null,
  });
}

export async function notifyStatusUpdate(label: string): Promise<void> {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'Lead atualizado',
      body: `Status alterado para "${label}".`,
      sound: 'default',
    },
    trigger: null,
  });
}
