export const ASSET_PAGE_SIZE = 120;

export type AssetSummary = {
	id: string;
	display_name: string;
	symbol: string;
	icon?: string;
	category?: string;
	tags?: string[];
};
