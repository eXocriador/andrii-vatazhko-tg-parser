import mongoose, { Schema, model, type InferSchemaType, type Model } from 'mongoose';

const mediaSchema = new Schema(
  {
    kind: { type: String, required: true },
    file_name: { type: String },
    mime_type: { type: String },
    size: { type: Number },
    caption: { type: String },
  },
  { _id: false },
);

const fundraiserSchema = new Schema(
  {
    uid: { type: String, required: true, unique: true },
    channelId: { type: Number, required: true },
    channelUsername: { type: String },
    messageId: { type: Number, required: true },
    title: { type: String },
    body: { type: String, required: true },
    originalPostedAt: { type: Date, required: true },
    collectedAt: { type: Date, required: true, default: () => new Date() },
    amountRequested: { type: Number },
    currency: { type: String },
    donationLinks: { type: [String], default: [] },
    tags: { type: [String], default: [] },
    media: { type: [mediaSchema], default: [] },
    sourceUrl: { type: String },
  },
  {
    timestamps: true,
  },
);

fundraiserSchema.index({ originalPostedAt: -1 });
fundraiserSchema.index({ createdAt: -1 });

export type FundraiserDocument = InferSchemaType<typeof fundraiserSchema>;

export const Fundraiser: Model<FundraiserDocument> =
  (mongoose.models.Fundraiser as Model<FundraiserDocument>) ??
  model<FundraiserDocument>('Fundraiser', fundraiserSchema);
