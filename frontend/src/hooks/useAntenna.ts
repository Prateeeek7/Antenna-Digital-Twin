import { useQuery } from '@tanstack/react-query';

export const useAntenna = (antennaId?: string) => {
  return useQuery({
    queryKey: ['antenna', antennaId],
    queryFn: async () => {
      // API calls are handled directly in components
      // This hook can be extended for shared antenna operations
      return null;
    },
    enabled: !!antennaId,
  });
};



















