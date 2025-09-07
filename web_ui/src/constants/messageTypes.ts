export const MESSAGE_TYPES = {
  0: 'Message',
  1: 'WebHook',
  2: 'Synology Chat'
} as const;

export type MessageType = keyof typeof MESSAGE_TYPES;

export const MESSAGE_TYPE_COLORS = {
  0: 'blue',
  1: 'orange',
  2: 'green'
} as const;