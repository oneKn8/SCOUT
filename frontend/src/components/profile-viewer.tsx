"use client"

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Calendar, Mail, Phone, MapPin, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'

interface ProfileData {
  schema_version: string
  generated_at: string
  extraction_method: string
  source_file: string
  contact?: {
    full_name?: string
    email?: string
    phone?: string
    location?: string
    website?: string
    linkedin?: string
    github?: string
  }
  summary?: {
    text?: string
    keywords?: string[]
  }
  experience?: Array<{
    company?: string
    position?: string
    location?: string
    dates?: {
      start_date?: string
      end_date?: string
      is_current?: boolean
      raw_date_text?: string
    }
    responsibilities?: string[]
    technologies?: string[]
    confidence_score?: number
  }>
  education?: Array<{
    institution?: string
    degree?: string
    field_of_study?: string
    location?: string
    dates?: {
      start_date?: string
      end_date?: string
      raw_date_text?: string
    }
    gpa?: string
    honors?: string[]
    confidence_score?: number
  }>
  skills?: Array<{
    name: string
    canonical_name?: string
    category?: string
    proficiency_level?: string
    years_experience?: number
    confidence_score?: number
  }>
  projects?: Array<{
    name: string
    description?: string
    url?: string
    dates?: {
      start_date?: string
      end_date?: string
    }
    technologies?: string[]
    role?: string
    confidence_score?: number
  }>
  achievements?: Array<{
    title: string
    organization?: string
    date_received?: string
    description?: string
    type?: string
  }>
  metadata?: {
    extractor_version: string
    extraction_timestamp: string
    confidence_score: number
    processing_time_ms?: number
    sections_detected?: string[]
  }
  warnings?: string[]
}

interface ProfileViewerProps {
  profile: ProfileData
  onBack?: () => void
}

export function ProfileViewer({ profile, onBack }: ProfileViewerProps) {
  const [showJsonViewer, setShowJsonViewer] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['contact', 'summary']))

  const toggleSection = (sectionName: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionName)) {
      newExpanded.delete(sectionName)
    } else {
      newExpanded.add(sectionName)
    }
    setExpandedSections(newExpanded)
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    if (dateStr === 'present' || dateStr === 'current') return 'Present'

    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
    } catch {
      return dateStr
    }
  }

  const formatDateRange = (dates?: { start_date?: string; end_date?: string; is_current?: boolean; raw_date_text?: string }) => {
    if (!dates) return ''
    if (dates.raw_date_text) return dates.raw_date_text

    const start = formatDate(dates.start_date)
    const end = dates.is_current ? 'Present' : formatDate(dates.end_date)

    if (start && end) return `${start} - ${end}`
    if (start) return start
    if (end) return end
    return ''
  }

  const getCategoryColor = (category?: string) => {
    const colors: Record<string, string> = {
      'programming': 'bg-blue-100 text-blue-800 hover:bg-blue-200',
      'frameworks': 'bg-green-100 text-green-800 hover:bg-green-200',
      'databases': 'bg-purple-100 text-purple-800 hover:bg-purple-200',
      'cloud': 'bg-orange-100 text-orange-800 hover:bg-orange-200',
      'tools': 'bg-gray-100 text-gray-800 hover:bg-gray-200',
      'technical': 'bg-indigo-100 text-indigo-800 hover:bg-indigo-200',
      'soft_skills': 'bg-pink-100 text-pink-800 hover:bg-pink-200',
      'certifications': 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200',
    }
    return colors[category || 'other'] || 'bg-slate-100 text-slate-800 hover:bg-slate-200'
  }

  const getConfidenceColor = (score?: number) => {
    if (!score) return 'bg-gray-100 text-gray-600'
    if (score >= 0.8) return 'bg-green-100 text-green-700'
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'
  }

  const SectionHeader = ({ title, count, isExpanded, onToggle }: {
    title: string
    count?: number
    isExpanded: boolean
    onToggle: () => void
  }) => (
    <Button
      variant="ghost"
      className="w-full justify-between p-0 h-auto font-semibold text-lg"
      onClick={onToggle}
    >
      <span>
        {title}
        {count !== undefined && (
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            ({count})
          </span>
        )}
      </span>
      {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
    </Button>
  )

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Resume Profile</h1>
          <p className="text-muted-foreground mt-1">
            Extracted from {profile.source_file} • {profile.extraction_method}
          </p>
        </div>
        <div className="flex gap-2">
          {onBack && (
            <Button variant="outline" onClick={onBack}>
              Back to Upload
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => setShowJsonViewer(!showJsonViewer)}
          >
            {showJsonViewer ? 'Hide JSON' : 'View JSON'}
          </Button>
        </div>
      </div>

      {/* Warnings */}
      {profile.warnings && profile.warnings.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="text-yellow-800 text-sm">Extraction Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1 text-sm text-yellow-700">
              {profile.warnings.map((warning, idx) => (
                <li key={idx}>{warning}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Contact Information */}
      {profile.contact && (
        <Card>
          <CardHeader>
            <SectionHeader
              title="Contact Information"
              isExpanded={expandedSections.has('contact')}
              onToggle={() => toggleSection('contact')}
            />
          </CardHeader>
          {expandedSections.has('contact') && (
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {profile.contact.full_name && (
                  <div className="text-2xl font-semibold col-span-full">
                    {profile.contact.full_name}
                  </div>
                )}

                {profile.contact.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <a href={`mailto:${profile.contact.email}`} className="hover:underline">
                      {profile.contact.email}
                    </a>
                  </div>
                )}

                {profile.contact.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span>{profile.contact.phone}</span>
                  </div>
                )}

                {profile.contact.location && (
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <span>{profile.contact.location}</span>
                  </div>
                )}

                {profile.contact.website && (
                  <div className="flex items-center gap-2">
                    <ExternalLink className="h-4 w-4 text-muted-foreground" />
                    <a href={profile.contact.website} target="_blank" rel="noopener noreferrer" className="hover:underline">
                      Website
                    </a>
                  </div>
                )}

                {profile.contact.linkedin && (
                  <div className="flex items-center gap-2">
                    <ExternalLink className="h-4 w-4 text-muted-foreground" />
                    <a href={profile.contact.linkedin} target="_blank" rel="noopener noreferrer" className="hover:underline">
                      LinkedIn
                    </a>
                  </div>
                )}

                {profile.contact.github && (
                  <div className="flex items-center gap-2">
                    <ExternalLink className="h-4 w-4 text-muted-foreground" />
                    <a href={profile.contact.github} target="_blank" rel="noopener noreferrer" className="hover:underline">
                      GitHub
                    </a>
                  </div>
                )}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Professional Summary */}
      {profile.summary?.text && (
        <Card>
          <CardHeader>
            <SectionHeader
              title="Professional Summary"
              isExpanded={expandedSections.has('summary')}
              onToggle={() => toggleSection('summary')}
            />
          </CardHeader>
          {expandedSections.has('summary') && (
            <CardContent>
              <p className="text-muted-foreground leading-relaxed">{profile.summary.text}</p>
              {profile.summary.keywords && profile.summary.keywords.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-medium mb-2">Key Terms:</h4>
                  <div className="flex flex-wrap gap-2">
                    {profile.summary.keywords.map((keyword, idx) => (
                      <Badge key={idx} variant="secondary">{keyword}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {/* Experience */}
      {profile.experience && profile.experience.length > 0 && (
        <Card>
          <CardHeader>
            <SectionHeader
              title="Work Experience"
              count={profile.experience.length}
              isExpanded={expandedSections.has('experience')}
              onToggle={() => toggleSection('experience')}
            />
          </CardHeader>
          {expandedSections.has('experience') && (
            <CardContent>
              <div className="space-y-6">
                {profile.experience.map((exp, idx) => (
                  <div key={idx} className="border-l-2 border-muted pl-4 relative">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold text-lg">{exp.position || 'Position Not Specified'}</h3>
                        <p className="text-muted-foreground">{exp.company || 'Company Not Specified'}</p>
                        {exp.location && <p className="text-sm text-muted-foreground">{exp.location}</p>}
                      </div>
                      <div className="text-right text-sm">
                        {exp.dates && (
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDateRange(exp.dates)}</span>
                          </div>
                        )}
                        {exp.confidence_score !== undefined && (
                          <Badge className={`text-xs ${getConfidenceColor(exp.confidence_score)}`}>
                            {Math.round(exp.confidence_score * 100)}% confidence
                          </Badge>
                        )}
                      </div>
                    </div>

                    {exp.responsibilities && exp.responsibilities.length > 0 && (
                      <div className="mb-3">
                        <h4 className="font-medium mb-2">Responsibilities:</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                          {exp.responsibilities.map((resp, respIdx) => (
                            <li key={respIdx}>{resp}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {exp.technologies && exp.technologies.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Technologies Used:</h4>
                        <div className="flex flex-wrap gap-1">
                          {exp.technologies.map((tech, techIdx) => (
                            <Badge key={techIdx} variant="outline" className="text-xs">
                              {tech}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Education */}
      {profile.education && profile.education.length > 0 && (
        <Card>
          <CardHeader>
            <SectionHeader
              title="Education"
              count={profile.education.length}
              isExpanded={expandedSections.has('education')}
              onToggle={() => toggleSection('education')}
            />
          </CardHeader>
          {expandedSections.has('education') && (
            <CardContent>
              <div className="space-y-4">
                {profile.education.map((edu, idx) => (
                  <div key={idx} className="border-l-2 border-muted pl-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold">{edu.degree || 'Degree Not Specified'}</h3>
                        {edu.field_of_study && <p className="text-muted-foreground">{edu.field_of_study}</p>}
                        <p className="text-muted-foreground">{edu.institution || 'Institution Not Specified'}</p>
                        {edu.location && <p className="text-sm text-muted-foreground">{edu.location}</p>}
                      </div>
                      <div className="text-right text-sm">
                        {edu.dates && (
                          <div>{formatDateRange(edu.dates)}</div>
                        )}
                        {edu.gpa && (
                          <div className="text-muted-foreground">GPA: {edu.gpa}</div>
                        )}
                      </div>
                    </div>

                    {edu.honors && edu.honors.length > 0 && (
                      <div className="mt-2">
                        <div className="flex flex-wrap gap-1">
                          {edu.honors.map((honor, honorIdx) => (
                            <Badge key={honorIdx} variant="secondary" className="text-xs">
                              {honor}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Skills */}
      {profile.skills && profile.skills.length > 0 && (
        <Card>
          <CardHeader>
            <SectionHeader
              title="Skills & Technologies"
              count={profile.skills.length}
              isExpanded={expandedSections.has('skills')}
              onToggle={() => toggleSection('skills')}
            />
          </CardHeader>
          {expandedSections.has('skills') && (
            <CardContent>
              <div className="space-y-4">
                {/* Group skills by category */}
                {Object.entries(
                  profile.skills.reduce((acc, skill) => {
                    const category = skill.category || 'other'
                    if (!acc[category]) acc[category] = []
                    acc[category].push(skill)
                    return acc
                  }, {} as Record<string, typeof profile.skills>)
                ).map(([category, categorySkills]) => (
                  <div key={category}>
                    <h4 className="font-medium mb-2 capitalize">
                      {category.replace('_', ' ')} ({categorySkills.length})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {categorySkills.map((skill, idx) => (
                        <Badge
                          key={idx}
                          className={getCategoryColor(skill.category)}
                          title={`${skill.canonical_name || skill.name}${skill.proficiency_level ? ` • ${skill.proficiency_level}` : ''}${skill.confidence_score ? ` • ${Math.round(skill.confidence_score * 100)}% confidence` : ''}`}
                        >
                          {skill.canonical_name || skill.name}
                          {skill.proficiency_level && (
                            <span className="ml-1 text-xs opacity-75">
                              • {skill.proficiency_level}
                            </span>
                          )}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Projects */}
      {profile.projects && profile.projects.length > 0 && (
        <Card>
          <CardHeader>
            <SectionHeader
              title="Projects"
              count={profile.projects.length}
              isExpanded={expandedSections.has('projects')}
              onToggle={() => toggleSection('projects')}
            />
          </CardHeader>
          {expandedSections.has('projects') && (
            <CardContent>
              <div className="space-y-4">
                {profile.projects.map((project, idx) => (
                  <div key={idx} className="border-l-2 border-muted pl-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold">{project.name}</h3>
                        {project.role && <p className="text-sm text-muted-foreground">Role: {project.role}</p>}
                      </div>
                      <div className="text-right text-sm">
                        {project.dates && (
                          <div>{formatDateRange(project.dates)}</div>
                        )}
                        {project.url && (
                          <a href={project.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            <ExternalLink className="inline h-3 w-3 ml-1" />
                          </a>
                        )}
                      </div>
                    </div>

                    {project.description && (
                      <p className="text-muted-foreground text-sm mb-2">{project.description}</p>
                    )}

                    {project.technologies && project.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {project.technologies.map((tech, techIdx) => (
                          <Badge key={techIdx} variant="outline" className="text-xs">
                            {tech}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Achievements */}
      {profile.achievements && profile.achievements.length > 0 && (
        <Card>
          <CardHeader>
            <SectionHeader
              title="Achievements & Awards"
              count={profile.achievements.length}
              isExpanded={expandedSections.has('achievements')}
              onToggle={() => toggleSection('achievements')}
            />
          </CardHeader>
          {expandedSections.has('achievements') && (
            <CardContent>
              <div className="space-y-3">
                {profile.achievements.map((achievement, idx) => (
                  <div key={idx} className="border-l-2 border-muted pl-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold">{achievement.title}</h3>
                        {achievement.organization && (
                          <p className="text-muted-foreground">{achievement.organization}</p>
                        )}
                        {achievement.description && (
                          <p className="text-sm text-muted-foreground mt-1">{achievement.description}</p>
                        )}
                      </div>
                      <div className="text-right text-sm">
                        {achievement.date_received && (
                          <div>{formatDate(achievement.date_received)}</div>
                        )}
                        {achievement.type && (
                          <Badge variant="secondary" className="text-xs mt-1">
                            {achievement.type}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Metadata */}
      <Card>
        <CardHeader>
          <SectionHeader
            title="Extraction Metadata"
            isExpanded={expandedSections.has('metadata')}
            onToggle={() => toggleSection('metadata')}
          />
        </CardHeader>
        {expandedSections.has('metadata') && profile.metadata && (
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Confidence Score:</span>
                <div className="mt-1">
                  <Badge className={getConfidenceColor(profile.metadata.confidence_score)}>
                    {Math.round(profile.metadata.confidence_score * 100)}%
                  </Badge>
                </div>
              </div>
              <div>
                <span className="font-medium">Processing Time:</span>
                <p className="text-muted-foreground">
                  {profile.metadata.processing_time_ms ? `${profile.metadata.processing_time_ms}ms` : 'Not recorded'}
                </p>
              </div>
              <div>
                <span className="font-medium">Extractor Version:</span>
                <p className="text-muted-foreground">{profile.metadata.extractor_version}</p>
              </div>
              <div>
                <span className="font-medium">Schema Version:</span>
                <p className="text-muted-foreground">{profile.schema_version}</p>
              </div>
              {profile.metadata.sections_detected && (
                <div className="col-span-2">
                  <span className="font-medium">Detected Sections:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {profile.metadata.sections_detected.map((section, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs">
                        {section}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>

      {/* JSON Viewer */}
      {showJsonViewer && (
        <Card>
          <CardHeader>
            <CardTitle>Raw Profile JSON</CardTitle>
            <CardDescription>
              Complete extracted profile data in JSON format
            </CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-md overflow-auto text-xs max-h-96">
              {JSON.stringify(profile, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}