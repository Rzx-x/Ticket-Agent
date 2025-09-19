import { extendTheme } from '@chakra-ui/react';
import { mode } from '@chakra-ui/theme-tools';

const config = {
  initialColorMode: 'light',
  useSystemColorMode: true,
};

const theme = extendTheme({
  config,
  fonts: {
    heading: 'var(--font-inter)',
    body: 'var(--font-inter)',
  },
  styles: {
    global: (props: any) => ({
      body: {
        bg: mode('gray.50', 'gray.900')(props),
        color: mode('gray.800', 'whiteAlpha.900')(props),
      },
    }),
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: 'semibold',
        borderRadius: 'xl',
      },
      variants: {
        solid: (props: any) => ({
          bg: mode('primary.500', 'primary.400')(props),
          color: 'white',
          _hover: {
            bg: mode('primary.600', 'primary.500')(props),
            transform: 'translateY(-1px)',
            boxShadow: 'lg',
          },
          _active: {
            bg: mode('primary.700', 'primary.600')(props),
            transform: 'translateY(0)',
          },
        }),
        outline: {
          borderWidth: '2px',
          _hover: {
            transform: 'translateY(-1px)',
            boxShadow: 'md',
          },
        },
        ghost: {
          _hover: {
            bg: 'whiteAlpha.200',
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    Card: {
      baseStyle: (props: any) => ({
        container: {
          bg: mode('white', 'gray.800')(props),
          borderRadius: 'xl',
          boxShadow: mode('sm', 'dark-lg')(props),
          overflow: 'hidden',
          transition: 'all 0.2s ease-in-out',
          _hover: {
            transform: 'translateY(-2px)',
            boxShadow: mode('md', 'dark-xl')(props),
          },
        },
      }),
    },
    Form: {
      baseStyle: {
        helperText: {
          color: 'gray.500',
          fontSize: 'sm',
          mt: 1,
        },
      },
    },
    Input: {
      defaultProps: {
        focusBorderColor: 'primary.500',
      },
      variants: {
        filled: (props: any) => ({
          field: {
            bg: mode('gray.100', 'whiteAlpha.50')(props),
            _hover: {
              bg: mode('gray.200', 'whiteAlpha.100')(props),
            },
            _focus: {
              bg: mode('white', 'whiteAlpha.100')(props),
            },
          },
        }),
      },
    },
  },
  colors: {
    primary: {
      50: '#eef8ff',
      100: '#d9edff',
      200: '#bce0ff',
      300: '#8ccbff',
      400: '#54adff',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },
    secondary: {
      50: '#faf5ff',
      100: '#f3e8ff',
      200: '#e9d5ff',
      300: '#d8b4fe',
      400: '#c084fc',
      500: '#a855f7',
      600: '#9333ea',
      700: '#7c3aed',
      800: '#6b21a8',
      900: '#581c87',
    },
    accent: {
      50: '#ecfeff',
      100: '#cffafe',
      200: '#a5f3fc',
      300: '#67e8f9',
      400: '#22d3ee',
      500: '#06b6d4',
      600: '#0891b2',
      700: '#0e7490',
      800: '#155e75',
      900: '#164e63',
    },
  },
  shadows: {
    outline: '0 0 0 3px rgba(59, 130, 246, 0.5)',
  },
  transition: {
    easing: {
      default: 'cubic-bezier(0.4, 0, 0.2, 1)',
      in: 'cubic-bezier(0.4, 0, 1, 1)',
      out: 'cubic-bezier(0, 0, 0.2, 1)',
      inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
    duration: {
      fast: '150ms',
      normal: '200ms',
      slow: '300ms',
      slower: '500ms',
    },
  },
});

export default theme;